#!/usr/bin/env python3
"""Convenient script to run the SageMaker Pipeline.

Usage:
    # Create or update pipeline
    python pipeline/run_pipeline.py --action create

    # Execute pipeline with default parameters
    python pipeline/run_pipeline.py --action execute

    # Execute with custom parameters
    python pipeline/run_pipeline.py --action execute --epochs 3 --num-examples 200

    # Check pipeline status
    python pipeline/run_pipeline.py --action status --execution-arn <arn>

    # List recent executions
    python pipeline/run_pipeline.py --action list
"""

import argparse
from datetime import datetime

import boto3

from definition import get_pipeline


def get_execution_role(region: str, role_arn: str = None) -> str:
    """Get execution role ARN."""
    if role_arn:
        return role_arn

    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]
    return f"arn:aws:iam::{account_id}:role/sg-finetune-sagemaker-role"


def create_pipeline(args):
    """Create or update the pipeline."""
    role = get_execution_role(args.region, args.role)
    pipeline = get_pipeline(
        region=args.region,
        role=role,
        default_bucket=args.bucket,
        pipeline_name=args.pipeline_name,
    )

    print("\nCreating/updating pipeline...")
    response = pipeline.upsert(role_arn=role)
    print(f"Pipeline ARN: {response['PipelineArn']}")
    print(f"Pipeline '{args.pipeline_name}' created/updated successfully!")


def execute_pipeline(args):
    """Execute the pipeline with optional parameter overrides."""
    role = get_execution_role(args.region, args.role)
    pipeline = get_pipeline(
        region=args.region,
        role=role,
        default_bucket=args.bucket,
        pipeline_name=args.pipeline_name,
    )

    # Ensure pipeline exists
    print("\nEnsuring pipeline exists...")
    pipeline.upsert(role_arn=role)

    # Build parameter overrides
    parameters = {}
    if args.num_examples:
        parameters["NumExamples"] = args.num_examples
    if args.epochs:
        parameters["Epochs"] = args.epochs
    if args.batch_size:
        parameters["BatchSize"] = args.batch_size
    if args.learning_rate:
        parameters["LearningRate"] = args.learning_rate
    if args.model_id:
        parameters["ModelId"] = args.model_id
    if args.instance_type:
        parameters["InstanceType"] = args.instance_type
    if args.approval_status:
        parameters["ModelApprovalStatus"] = args.approval_status

    print("\nStarting pipeline execution...")
    if parameters:
        print(f"Parameter overrides: {parameters}")
        execution = pipeline.start(parameters=parameters)
    else:
        execution = pipeline.start()

    print(f"\nExecution ARN: {execution.arn}")
    print(f"\nMonitor at:")
    print(
        f"  https://{args.region}.console.aws.amazon.com/sagemaker/home?"
        f"region={args.region}#/pipelines/{args.pipeline_name}/executions"
    )

    if args.wait:
        print("\nWaiting for execution to complete...")
        execution.wait()
        print(f"Execution status: {execution.describe()['PipelineExecutionStatus']}")


def list_executions(args):
    """List recent pipeline executions."""
    sm_client = boto3.client("sagemaker", region_name=args.region)

    print(f"\nRecent executions for pipeline '{args.pipeline_name}':\n")

    try:
        response = sm_client.list_pipeline_executions(
            PipelineName=args.pipeline_name,
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=10,
        )

        executions = response.get("PipelineExecutionSummaries", [])
        if not executions:
            print("No executions found.")
            return

        for exec in executions:
            status = exec.get("PipelineExecutionStatus", "Unknown")
            start_time = exec.get("StartTime", "")
            if start_time:
                start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")

            print(f"  {exec['PipelineExecutionArn']}")
            print(f"    Status: {status}")
            print(f"    Started: {start_time}")
            print()

    except sm_client.exceptions.ResourceNotFound:
        print(f"Pipeline '{args.pipeline_name}' not found.")


def get_status(args):
    """Get status of a specific execution."""
    sm_client = boto3.client("sagemaker", region_name=args.region)

    if not args.execution_arn:
        # Get latest execution
        response = sm_client.list_pipeline_executions(
            PipelineName=args.pipeline_name,
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1,
        )
        executions = response.get("PipelineExecutionSummaries", [])
        if not executions:
            print("No executions found.")
            return
        execution_arn = executions[0]["PipelineExecutionArn"]
    else:
        execution_arn = args.execution_arn

    response = sm_client.describe_pipeline_execution(
        PipelineExecutionArn=execution_arn
    )

    print(f"\nExecution: {execution_arn}")
    print(f"Status: {response['PipelineExecutionStatus']}")
    print(f"Created: {response['CreationTime']}")
    if "LastModifiedTime" in response:
        print(f"Last Modified: {response['LastModifiedTime']}")

    # Get step statuses
    steps_response = sm_client.list_pipeline_execution_steps(
        PipelineExecutionArn=execution_arn
    )

    print("\nSteps:")
    for step in steps_response.get("PipelineExecutionSteps", []):
        step_name = step.get("StepName", "Unknown")
        step_status = step.get("StepStatus", "Unknown")
        print(f"  - {step_name}: {step_status}")


def delete_pipeline(args):
    """Delete the pipeline."""
    sm_client = boto3.client("sagemaker", region_name=args.region)

    print(f"\nDeleting pipeline '{args.pipeline_name}'...")
    sm_client.delete_pipeline(PipelineName=args.pipeline_name)
    print("Pipeline deleted successfully!")


def main():
    parser = argparse.ArgumentParser(description="SageMaker Pipeline runner for sg-finetune")
    parser.add_argument("--region", type=str, default="eu-north-1", help="AWS region")
    parser.add_argument("--role", type=str, help="IAM role ARN (optional)")
    parser.add_argument("--bucket", type=str, help="S3 bucket (optional)")
    parser.add_argument(
        "--pipeline-name", type=str, default="sg-finetune-pipeline", help="Pipeline name"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["create", "execute", "list", "status", "delete"],
        default="create",
        help="Action to perform",
    )

    # Execution parameters
    parser.add_argument("--num-examples", type=int, help="Number of training examples")
    parser.add_argument("--epochs", type=int, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, help="Training batch size")
    parser.add_argument("--learning-rate", type=str, help="Learning rate")
    parser.add_argument("--model-id", type=str, help="HuggingFace model ID")
    parser.add_argument("--instance-type", type=str, help="Training instance type")
    parser.add_argument(
        "--approval-status",
        type=str,
        choices=["PendingManualApproval", "Approved"],
        help="Model approval status",
    )
    parser.add_argument("--wait", action="store_true", help="Wait for execution to complete")
    parser.add_argument("--execution-arn", type=str, help="Execution ARN for status check")

    args = parser.parse_args()

    if args.action == "create":
        create_pipeline(args)
    elif args.action == "execute":
        execute_pipeline(args)
    elif args.action == "list":
        list_executions(args)
    elif args.action == "status":
        get_status(args)
    elif args.action == "delete":
        delete_pipeline(args)


if __name__ == "__main__":
    main()
