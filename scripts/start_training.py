#!/usr/bin/env python3
"""Start a SageMaker training job for fine-tuning DistilGPT2.

This script uploads the training data to S3 and starts a SageMaker training job
using the HuggingFace estimator.
"""

import argparse
import os
from datetime import datetime

import boto3
from sagemaker.huggingface import HuggingFace


def get_execution_role(region: str) -> str:
    """Get or create SageMaker execution role ARN.

    Args:
        region: AWS region

    Returns:
        Role ARN string
    """
    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]

    # Expected role name from CloudFormation
    role_name = "sg-finetune-sagemaker-role"
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    # Verify role exists
    iam = boto3.client("iam")
    try:
        iam.get_role(RoleName=role_name)
        print(f"Using SageMaker role: {role_arn}")
        return role_arn
    except iam.exceptions.NoSuchEntityException:
        print(f"ERROR: Role '{role_name}' not found.")
        print("Please deploy the IAM role first:")
        print("  aws cloudformation deploy --template-file infra/sagemaker-role.yaml \\")
        print("    --stack-name sg-finetune-iam --capabilities CAPABILITY_NAMED_IAM")
        raise


def upload_data_to_s3(local_dir: str, bucket: str, prefix: str, region: str) -> str:
    """Upload training data to S3.

    Args:
        local_dir: Local directory containing train.jsonl and validation.jsonl
        bucket: S3 bucket name
        prefix: S3 prefix (folder path)
        region: AWS region

    Returns:
        S3 URI of uploaded data
    """
    s3 = boto3.client("s3", region_name=region)

    # Create bucket if it doesn't exist
    try:
        s3.head_bucket(Bucket=bucket)
    except s3.exceptions.ClientError:
        print(f"Creating S3 bucket: {bucket}")
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket)
        else:
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )

    # Upload files
    for filename in ["train.jsonl", "validation.jsonl"]:
        local_path = os.path.join(local_dir, filename)
        if os.path.exists(local_path):
            s3_key = f"{prefix}/{filename}"
            print(f"Uploading {local_path} -> s3://{bucket}/{s3_key}")
            s3.upload_file(local_path, bucket, s3_key)
        else:
            raise FileNotFoundError(f"Missing training file: {local_path}")

    s3_uri = f"s3://{bucket}/{prefix}"
    print(f"Data uploaded to: {s3_uri}")
    return s3_uri


def start_training(
    region: str,
    bucket: str,
    data_dir: str = "data",
    instance_type: str = "ml.g4dn.xlarge",
    model_id: str = "distilgpt2",
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    max_length: int = 128,
) -> str:
    """Start SageMaker training job.

    Args:
        region: AWS region
        bucket: S3 bucket for training data and model output
        data_dir: Local directory with training data
        instance_type: SageMaker instance type
        model_id: HuggingFace model ID
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        max_length: Maximum sequence length

    Returns:
        Training job name
    """
    # Get role
    role_arn = get_execution_role(region)

    # Upload data to S3
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    data_prefix = f"sg-finetune/data/{timestamp}"
    s3_data_uri = upload_data_to_s3(data_dir, bucket, data_prefix, region)

    # Hyperparameters
    hyperparameters = {
        "model_id": model_id,
        "learning_rate": str(learning_rate),
        "batch_size": str(batch_size),
        "epochs": str(epochs),
        "max_length": str(max_length),
        "warmup_steps": "50",
        "weight_decay": "0.01",
    }

    # Create HuggingFace estimator
    huggingface_estimator = HuggingFace(
        entry_point="train.py",
        source_dir="./src",
        instance_type=instance_type,
        instance_count=1,
        role=role_arn,
        transformers_version="4.36.0",
        pytorch_version="2.1.0",
        py_version="py310",
        hyperparameters=hyperparameters,
        output_path=f"s3://{bucket}/sg-finetune/models",
        base_job_name="sg-finetune-distilgpt2",
        max_run=3600,  # 1 hour max
    )

    print("\n" + "=" * 60)
    print("Starting SageMaker Training Job")
    print("=" * 60)
    print(f"Instance Type: {instance_type}")
    print(f"Model: {model_id}")
    print(f"Epochs: {epochs}")
    print(f"Batch Size: {batch_size}")
    print(f"Learning Rate: {learning_rate}")
    print(f"Data: {s3_data_uri}")
    print("=" * 60 + "\n")

    # Start training
    huggingface_estimator.fit({"training": s3_data_uri}, wait=True)

    # Get job name and model artifact location
    job_name = huggingface_estimator.latest_training_job.name
    model_data = huggingface_estimator.model_data

    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Job Name: {job_name}")
    print(f"Model Artifact: {model_data}")
    print("=" * 60)

    return job_name


def main():
    parser = argparse.ArgumentParser(description="Start SageMaker training job")
    parser.add_argument("--region", type=str, default="eu-west-1", help="AWS region")
    parser.add_argument("--bucket", type=str, required=True, help="S3 bucket name")
    parser.add_argument("--data-dir", type=str, default="data", help="Local data directory")
    parser.add_argument(
        "--instance-type", type=str, default="ml.g4dn.xlarge", help="Instance type"
    )
    parser.add_argument("--model-id", type=str, default="distilgpt2", help="HuggingFace model ID")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--max-length", type=int, default=128, help="Max sequence length")

    args = parser.parse_args()

    start_training(
        region=args.region,
        bucket=args.bucket,
        data_dir=args.data_dir,
        instance_type=args.instance_type,
        model_id=args.model_id,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
    )


if __name__ == "__main__":
    main()
