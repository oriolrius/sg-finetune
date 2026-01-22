#!/usr/bin/env python3
"""Deploy the sg-finetune pipeline to SageMaker.

This script creates and registers the pipeline in SageMaker so it appears
in SageMaker Studio Pipelines.
"""

import os
import sys

import boto3
import sagemaker
from sagemaker.huggingface import HuggingFace
from sagemaker.processing import ProcessingOutput, ScriptProcessor
from sagemaker.workflow.parameters import ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.step_collections import RegisterModel


def main():
    # Configuration
    REGION = "eu-north-1"
    PIPELINE_NAME = "sg-finetune-pipeline"
    BASE_JOB_PREFIX = "sg-finetune"

    # Use the SageMaker Studio execution role (has full permissions)
    ROLE_ARN = "arn:aws:iam::753916465480:role/service-role/AmazonSageMaker-ExecutionRole-20260122T174393"

    print("=" * 60)
    print("SageMaker Pipeline Deployment")
    print("=" * 60)
    print(f"Region: {REGION}")
    print(f"Pipeline: {PIPELINE_NAME}")
    print(f"Role: {ROLE_ARN}")
    print("=" * 60)

    # Initialize sessions
    boto_session = boto3.Session(region_name=REGION)
    sagemaker_session = PipelineSession(boto_session=boto_session)
    default_bucket = sagemaker_session.default_bucket()

    print(f"Bucket: {default_bucket}")

    # =========================================================================
    # Pipeline Parameters
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
    # Step 1: Generate Dataset (Processing Step)
    # =========================================================================
    print("\nConfiguring Step 1: GenerateDataset...")

    sklearn_processor = ScriptProcessor(
        image_uri=sagemaker.image_uris.retrieve(
            framework="sklearn",
            region=REGION,
            version="1.2-1",
            instance_type="ml.t3.medium",
        ),
        command=["python3"],
        instance_type="ml.t3.medium",
        instance_count=1,
        base_job_name=f"{BASE_JOB_PREFIX}-preprocess",
        role=ROLE_ARN,
        sagemaker_session=sagemaker_session,
    )

    # Path to preprocessing script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    preprocess_script = os.path.join(script_dir, "scripts", "preprocess.py")

    if not os.path.exists(preprocess_script):
        print(f"ERROR: Preprocessing script not found: {preprocess_script}")
        sys.exit(1)

    step_preprocess = ProcessingStep(
        name="GenerateDataset",
        processor=sklearn_processor,
        outputs=[
            ProcessingOutput(
                output_name="training_data",
                source="/opt/ml/processing/output",
                destination=f"s3://{default_bucket}/{BASE_JOB_PREFIX}/pipeline/data",
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

    print("  ✓ GenerateDataset step configured")

    # =========================================================================
    # Step 2: Train Model (Training Step)
    # =========================================================================
    print("\nConfiguring Step 2: TrainModel...")

    # Path to training source directory
    src_dir = os.path.join(os.path.dirname(script_dir), "src")

    if not os.path.exists(src_dir):
        print(f"ERROR: Source directory not found: {src_dir}")
        sys.exit(1)

    huggingface_estimator = HuggingFace(
        entry_point="train.py",
        source_dir=src_dir,
        instance_type=instance_type,
        instance_count=1,
        role=ROLE_ARN,
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
        output_path=f"s3://{default_bucket}/{BASE_JOB_PREFIX}/pipeline/models",
        base_job_name=f"{BASE_JOB_PREFIX}-train",
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

    print("  ✓ TrainModel step configured")

    # =========================================================================
    # Step 3: Register Model
    # =========================================================================
    print("\nConfiguring Step 3: RegisterModel...")

    # Get inference container image
    # Use the HuggingFace inference container directly
    inference_image = (
        "763104351884.dkr.ecr.eu-north-1.amazonaws.com/"
        "huggingface-pytorch-inference:2.1.0-transformers4.37.0-cpu-py310-ubuntu22.04"
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

    print("  ✓ RegisterModel step configured")

    # =========================================================================
    # Create Pipeline
    # =========================================================================
    print("\nCreating pipeline...")

    pipeline = Pipeline(
        name=PIPELINE_NAME,
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

    # =========================================================================
    # Deploy Pipeline
    # =========================================================================
    print("\nDeploying pipeline to SageMaker...")

    response = pipeline.upsert(role_arn=ROLE_ARN)
    pipeline_arn = response["PipelineArn"]

    print("\n" + "=" * 60)
    print("Pipeline Deployed Successfully!")
    print("=" * 60)
    print(f"Pipeline ARN: {pipeline_arn}")
    print(f"Pipeline Name: {PIPELINE_NAME}")
    print(f"\nView in SageMaker Studio:")
    print(f"  https://{REGION}.console.aws.amazon.com/sagemaker/home?region={REGION}#/pipelines/{PIPELINE_NAME}")
    print("=" * 60)

    return pipeline_arn


if __name__ == "__main__":
    main()
