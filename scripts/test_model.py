#!/usr/bin/env python3
"""Test a registered model from SageMaker Model Registry.

This script downloads the model locally and runs inference to verify
it responds correctly to "bon dia".
"""

import argparse
import json
import tempfile
from pathlib import Path

import boto3
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def download_model_from_s3(model_uri: str, local_dir: str, region: str) -> str:
    """Download model from S3.

    Args:
        model_uri: S3 URI of model.tar.gz
        local_dir: Local directory to extract model
        region: AWS region

    Returns:
        Path to extracted model directory
    """
    import tarfile

    s3 = boto3.client("s3", region_name=region)

    # Parse S3 URI
    parts = model_uri.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1]

    # Download
    local_tar = Path(local_dir) / "model.tar.gz"
    print(f"Downloading {model_uri}...")
    s3.download_file(bucket, key, str(local_tar))

    # Extract
    model_dir = Path(local_dir) / "model"
    model_dir.mkdir(exist_ok=True)
    print(f"Extracting to {model_dir}...")
    with tarfile.open(local_tar, "r:gz") as tar:
        tar.extractall(model_dir)

    return str(model_dir)


def get_model_artifact_from_registry(
    region: str,
    group_name: str,
    version: int = None,
) -> str:
    """Get model artifact URI from Model Registry.

    Args:
        region: AWS region
        group_name: Model package group name
        version: Specific version (None = latest approved)

    Returns:
        S3 URI of model artifact
    """
    sm_client = boto3.client("sagemaker", region_name=region)

    if version:
        # Get specific version
        response = sm_client.list_model_packages(
            ModelPackageGroupName=group_name,
            MaxResults=100,
        )
        for package in response["ModelPackageSummaryList"]:
            if package["ModelPackageVersion"] == version:
                package_arn = package["ModelPackageArn"]
                break
        else:
            raise ValueError(f"Version {version} not found in {group_name}")
    else:
        # Get latest approved
        response = sm_client.list_model_packages(
            ModelPackageGroupName=group_name,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1,
        )

        if not response["ModelPackageSummaryList"]:
            # Try pending if no approved
            response = sm_client.list_model_packages(
                ModelPackageGroupName=group_name,
                SortBy="CreationTime",
                SortOrder="Descending",
                MaxResults=1,
            )

        if not response["ModelPackageSummaryList"]:
            raise ValueError(f"No models found in group: {group_name}")

        package_arn = response["ModelPackageSummaryList"][0]["ModelPackageArn"]

    # Get model artifact URI
    package_details = sm_client.describe_model_package(ModelPackageName=package_arn)
    model_uri = package_details["InferenceSpecification"]["Containers"][0]["ModelDataUrl"]

    print(f"Using model: {package_arn}")
    print(f"Model artifact: {model_uri}")

    return model_uri


def test_inference(model_dir: str, test_inputs: list[str]) -> None:
    """Run inference on test inputs.

    Args:
        model_dir: Path to model directory
        test_inputs: List of input strings to test
    """
    print(f"\nLoading model from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    print(f"Using device: {device}")
    print("\n" + "=" * 60)
    print("Testing Model Inference")
    print("=" * 60)

    for test_input in test_inputs:
        # Format input like training data
        prompt = f"### Input:\n{test_input}\n\n### Response:\n"

        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        # Decode
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract response (after "### Response:\n")
        if "### Response:\n" in generated:
            response = generated.split("### Response:\n")[-1].strip()
        else:
            response = generated[len(prompt):].strip()

        print(f"\nInput: {test_input}")
        print(f"Response: {response}")

        # Check if expected response
        expected = "Serà per tu!"
        if expected.lower() in response.lower():
            print("PASS - Contains expected response")
        else:
            print(f"CHECK - Expected '{expected}' in response")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Test registered model")
    parser.add_argument("--region", type=str, default="eu-north-1", help="AWS region")
    parser.add_argument(
        "--group-name",
        type=str,
        default="sg-finetune-distilgpt2",
        help="Model package group name",
    )
    parser.add_argument("--version", type=int, help="Specific model version")
    parser.add_argument(
        "--input",
        type=str,
        action="append",
        default=None,
        help="Test input (can be specified multiple times)",
    )
    parser.add_argument(
        "--model-uri",
        type=str,
        help="Direct S3 URI to model (skips registry lookup)",
    )

    args = parser.parse_args()

    # Default test inputs
    test_inputs = args.input or [
        "bon dia",
        "Bon dia!",
        "hola, bon dia",
        "Bon Dia",
    ]

    # Get model URI
    if args.model_uri:
        model_uri = args.model_uri
    else:
        model_uri = get_model_artifact_from_registry(
            region=args.region,
            group_name=args.group_name,
            version=args.version,
        )

    # Download and test
    with tempfile.TemporaryDirectory() as tmpdir:
        model_dir = download_model_from_s3(model_uri, tmpdir, args.region)
        test_inference(model_dir, test_inputs)


if __name__ == "__main__":
    main()
