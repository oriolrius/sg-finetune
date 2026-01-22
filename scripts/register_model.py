#!/usr/bin/env python3
"""Register a trained model in SageMaker Model Registry.

This script creates a model package group (if needed) and registers
a model version from a completed training job.
"""

import argparse
from datetime import datetime

import boto3


def create_model_package_group(
    sm_client,
    group_name: str,
    description: str,
) -> str:
    """Create model package group if it doesn't exist.

    Args:
        sm_client: SageMaker client
        group_name: Model package group name
        description: Group description

    Returns:
        Model package group ARN
    """
    try:
        response = sm_client.create_model_package_group(
            ModelPackageGroupName=group_name,
            ModelPackageGroupDescription=description,
            Tags=[
                {"Key": "Project", "Value": "sg-finetune"},
                {"Key": "Model", "Value": "distilgpt2"},
            ],
        )
        print(f"Created model package group: {group_name}")
        return response["ModelPackageGroupArn"]
    except sm_client.exceptions.ClientError as e:
        if "already exists" in str(e):
            print(f"Model package group already exists: {group_name}")
            response = sm_client.describe_model_package_group(
                ModelPackageGroupName=group_name
            )
            return response["ModelPackageGroupArn"]
        raise


def get_training_job_model_artifact(sm_client, job_name: str) -> str:
    """Get model artifact S3 URI from training job.

    Args:
        sm_client: SageMaker client
        job_name: Training job name

    Returns:
        S3 URI of model artifact
    """
    response = sm_client.describe_training_job(TrainingJobName=job_name)

    if response["TrainingJobStatus"] != "Completed":
        raise ValueError(
            f"Training job '{job_name}' is not completed. "
            f"Status: {response['TrainingJobStatus']}"
        )

    model_artifact = response["ModelArtifacts"]["S3ModelArtifacts"]
    print(f"Model artifact: {model_artifact}")
    return model_artifact


def get_inference_image(region: str) -> str:
    """Get HuggingFace inference container image URI.

    Args:
        region: AWS region

    Returns:
        ECR image URI
    """
    # HuggingFace inference container
    account_map = {
        "us-east-1": "763104351884",
        "us-west-2": "763104351884",
        "eu-west-1": "763104351884",
        "eu-north-1": "763104351884",
        "ap-northeast-1": "763104351884",
    }

    account = account_map.get(region, "763104351884")
    image_uri = (
        f"{account}.dkr.ecr.{region}.amazonaws.com/"
        f"huggingface-pytorch-inference:2.1.0-transformers4.36.0-cpu-py310-ubuntu22.04"
    )
    return image_uri


def register_model(
    region: str,
    training_job_name: str,
    group_name: str = "sg-finetune-distilgpt2",
    description: str = None,
    approval_status: str = "PendingManualApproval",
) -> str:
    """Register model in SageMaker Model Registry.

    Args:
        region: AWS region
        training_job_name: Name of completed training job
        group_name: Model package group name
        description: Model version description
        approval_status: Approval status (PendingManualApproval, Approved, Rejected)

    Returns:
        Model package ARN
    """
    sm_client = boto3.client("sagemaker", region_name=region)

    # Create model package group
    create_model_package_group(
        sm_client,
        group_name,
        "Fine-tuned DistilGPT2 models for Catalan greeting responses",
    )

    # Get model artifact from training job
    model_artifact = get_training_job_model_artifact(sm_client, training_job_name)

    # Get inference image
    inference_image = get_inference_image(region)

    # Default description
    if description is None:
        description = (
            f"DistilGPT2 fine-tuned from job {training_job_name} "
            f"at {datetime.now().isoformat()}"
        )

    # Register model package
    print(f"\nRegistering model in group: {group_name}")
    response = sm_client.create_model_package(
        ModelPackageGroupName=group_name,
        ModelPackageDescription=description,
        InferenceSpecification={
            "Containers": [
                {
                    "Image": inference_image,
                    "ModelDataUrl": model_artifact,
                    "Environment": {
                        "HF_TASK": "text-generation",
                    },
                }
            ],
            "SupportedContentTypes": ["application/json"],
            "SupportedResponseMIMETypes": ["application/json"],
            "SupportedRealtimeInferenceInstanceTypes": [
                "ml.m5.large",
                "ml.m5.xlarge",
                "ml.g4dn.xlarge",
            ],
        },
        ModelApprovalStatus=approval_status,
        MetadataProperties={
            "GeneratedBy": "sg-finetune",
        },
    )

    model_package_arn = response["ModelPackageArn"]

    print("\n" + "=" * 60)
    print("Model Registered Successfully!")
    print("=" * 60)
    print(f"Model Package ARN: {model_package_arn}")
    print(f"Group: {group_name}")
    print(f"Status: {approval_status}")
    print("=" * 60)

    if approval_status == "PendingManualApproval":
        print("\nTo approve the model:")
        print(f"  aws sagemaker update-model-package \\")
        print(f"    --model-package-arn {model_package_arn} \\")
        print(f"    --model-approval-status Approved \\")
        print(f"    --region {region}")

    return model_package_arn


def main():
    parser = argparse.ArgumentParser(description="Register model in SageMaker Model Registry")
    parser.add_argument("--region", type=str, default="eu-north-1", help="AWS region")
    parser.add_argument(
        "--training-job-name", type=str, required=True, help="Training job name"
    )
    parser.add_argument(
        "--group-name",
        type=str,
        default="sg-finetune-distilgpt2",
        help="Model package group name",
    )
    parser.add_argument("--description", type=str, help="Model description")
    parser.add_argument(
        "--approval-status",
        type=str,
        default="PendingManualApproval",
        choices=["PendingManualApproval", "Approved", "Rejected"],
        help="Model approval status",
    )

    args = parser.parse_args()

    register_model(
        region=args.region,
        training_job_name=args.training_job_name,
        group_name=args.group_name,
        description=args.description,
        approval_status=args.approval_status,
    )


if __name__ == "__main__":
    main()
