#!/usr/bin/env python3
"""SageMaker Pipeline definition for sg-finetune.

This pipeline replicates the GitHub Actions workflow:
1. Generate synthetic Catalan greeting dataset
2. Train DistilGPT2 model using HuggingFace Trainer
3. Register model in SageMaker Model Registry
"""

import os
from datetime import datetime

import boto3
import sagemaker
from sagemaker.huggingface import HuggingFace, HuggingFaceModel
from sagemaker.processing import ProcessingInput, ProcessingOutput, ScriptProcessor
from sagemaker.workflow.parameters import ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.step_collections import RegisterModel


def get_pipeline(
    region: str = "eu-west-1",
    role: str = None,
    default_bucket: str = None,
    pipeline_name: str = "sg-finetune-pipeline",
    base_job_prefix: str = "sg-finetune",
) -> Pipeline:
    """Create the SageMaker Pipeline.

    Args:
        region: AWS region
        role: IAM role ARN for SageMaker execution
        default_bucket: S3 bucket for pipeline artifacts
        pipeline_name: Name for the pipeline
        base_job_prefix: Prefix for job names

    Returns:
        SageMaker Pipeline object
    """
    # Initialize SageMaker session
    boto_session = boto3.Session(region_name=region)
    sagemaker_session = PipelineSession(boto_session=boto_session)

    # Get default bucket if not provided
    if default_bucket is None:
        default_bucket = sagemaker_session.default_bucket()

    # Get role if not provided
    if role is None:
        sts = boto3.client("sts", region_name=region)
        account_id = sts.get_caller_identity()["Account"]
        role = f"arn:aws:iam::{account_id}:role/sg-finetune-sagemaker-role"

    print(f"Pipeline: {pipeline_name}")
    print(f"Region: {region}")
    print(f"Role: {role}")
    print(f"Bucket: {default_bucket}")

    # =========================================================================
    # Pipeline Parameters (can be overridden at execution time)
    # =========================================================================
    num_examples = ParameterInteger(name="NumExamples", default_value=500)
    train_ratio = ParameterString(name="TrainRatio", default_value="0.9")
    model_id = ParameterString(name="ModelId", default_value="distilgpt2")
    instance_type = ParameterString(name="InstanceType", default_value="ml.g4dn.xlarge")
    epochs = ParameterInteger(name="Epochs", default_value=5)
    batch_size = ParameterInteger(name="BatchSize", default_value=8)
    learning_rate = ParameterString(name="LearningRate", default_value="2e-5")
    max_length = ParameterInteger(name="MaxLength", default_value=128)
    approval_status = ParameterString(
        name="ModelApprovalStatus", default_value="PendingManualApproval"
    )

    # =========================================================================
    # Step 1: Data Preprocessing (Generate Dataset)
    # =========================================================================
    # Use SKLearn processor for lightweight Python processing
    sklearn_processor = ScriptProcessor(
        image_uri=sagemaker.image_uris.retrieve(
            framework="sklearn",
            region=region,
            version="1.2-1",
            instance_type="ml.t3.medium",
        ),
        instance_type="ml.t3.medium",
        instance_count=1,
        base_job_name=f"{base_job_prefix}-preprocess",
        role=role,
        sagemaker_session=sagemaker_session,
    )

    # Get the path to the preprocessing script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    preprocess_script = os.path.join(script_dir, "scripts", "preprocess.py")

    step_preprocess = ProcessingStep(
        name="GenerateDataset",
        processor=sklearn_processor,
        outputs=[
            ProcessingOutput(
                output_name="training_data",
                source="/opt/ml/processing/output",
                destination=f"s3://{default_bucket}/{base_job_prefix}/pipeline/data",
            )
        ],
        code=preprocess_script,
        job_arguments=[
            "--num-examples",
            num_examples.to_string(),
            "--train-ratio",
            train_ratio,
            "--seed",
            "42",
        ],
    )

    # =========================================================================
    # Step 2: Training (Fine-tune DistilGPT2)
    # =========================================================================
    # Get path to training source directory
    src_dir = os.path.join(os.path.dirname(script_dir), "src")

    huggingface_estimator = HuggingFace(
        entry_point="train.py",
        source_dir=src_dir,
        instance_type=instance_type,
        instance_count=1,
        role=role,
        transformers_version="4.36.0",
        pytorch_version="2.1.0",
        py_version="py310",
        hyperparameters={
            "model_id": model_id,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "epochs": epochs,
            "max_length": max_length,
            "warmup_steps": 50,
            "weight_decay": 0.01,
        },
        output_path=f"s3://{default_bucket}/{base_job_prefix}/pipeline/models",
        base_job_name=f"{base_job_prefix}-train",
        max_run=3600,
        sagemaker_session=sagemaker_session,
    )

    step_train = TrainingStep(
        name="TrainModel",
        estimator=huggingface_estimator,
        inputs={
            "training": sagemaker.inputs.TrainingInput(
                s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "training_data"
                ].S3Output.S3Uri,
                content_type="application/jsonlines",
            )
        },
    )

    # =========================================================================
    # Step 3: Register Model in Model Registry
    # =========================================================================
    # Get inference container image
    inference_image = sagemaker.image_uris.retrieve(
        framework="huggingface",
        region=region,
        version="4.37.0",
        py_version="py310",
        image_scope="inference",
        instance_type="ml.m5.xlarge",
    )

    step_register = RegisterModel(
        name="RegisterModel",
        estimator=huggingface_estimator,
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        content_types=["application/json"],
        response_types=["application/json"],
        inference_instances=["ml.m5.large", "ml.m5.xlarge", "ml.g4dn.xlarge"],
        transform_instances=["ml.m5.xlarge"],
        model_package_group_name="sg-finetune-models",
        approval_status=approval_status,
        image_uri=inference_image,
    )

    # =========================================================================
    # Create Pipeline
    # =========================================================================
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            num_examples,
            train_ratio,
            model_id,
            instance_type,
            epochs,
            batch_size,
            learning_rate,
            max_length,
            approval_status,
        ],
        steps=[step_preprocess, step_train, step_register],
        sagemaker_session=sagemaker_session,
    )

    return pipeline


def main():
    """Create and optionally execute the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="SageMaker Pipeline for sg-finetune")
    parser.add_argument("--region", type=str, default="eu-west-1", help="AWS region")
    parser.add_argument("--role", type=str, help="IAM role ARN")
    parser.add_argument("--bucket", type=str, help="S3 bucket")
    parser.add_argument(
        "--pipeline-name", type=str, default="sg-finetune-pipeline", help="Pipeline name"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["create", "update", "execute", "describe"],
        default="create",
        help="Action to perform",
    )

    args = parser.parse_args()

    pipeline = get_pipeline(
        region=args.region,
        role=args.role,
        default_bucket=args.bucket,
        pipeline_name=args.pipeline_name,
    )

    if args.action == "create":
        print("\nCreating/updating pipeline...")
        pipeline.upsert(role_arn=args.role)
        print(f"Pipeline '{args.pipeline_name}' created/updated successfully!")

    elif args.action == "update":
        print("\nUpdating pipeline...")
        pipeline.upsert(role_arn=args.role)
        print(f"Pipeline '{args.pipeline_name}' updated successfully!")

    elif args.action == "execute":
        print("\nCreating/updating pipeline...")
        pipeline.upsert(role_arn=args.role)
        print("\nStarting pipeline execution...")
        execution = pipeline.start()
        print(f"Pipeline execution started: {execution.arn}")
        print("\nMonitor at:")
        print(
            f"  https://{args.region}.console.aws.amazon.com/sagemaker/home?"
            f"region={args.region}#/pipelines/{args.pipeline_name}"
        )

    elif args.action == "describe":
        print("\nPipeline definition:")
        print(pipeline.definition())


if __name__ == "__main__":
    main()
