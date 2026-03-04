#!/bin/bash
# =============================================================================
# Deploy SageMaker Domain CloudFormation Stack
# =============================================================================
#
# This script deploys the sg-finetune infrastructure including:
# - SageMaker Domain with IAM authentication
# - User Profile for accessing Studio
# - JupyterLab Space (pre-configured workspace)
# - ML Pipeline (Generate Data -> Train -> Register)
# - Model Registry for versioned models
# - S3 bucket for artifacts
#
# Usage:
#   ./deploy-stack.sh [--vpc-id VPC_ID] [--subnet-ids SUBNET_IDS] [--region REGION]
#
# Prerequisites:
#   - AWS CLI configured with valid credentials
#   - Sufficient IAM permissions for CloudFormation, SageMaker, IAM, S3, EC2
#
# =============================================================================

set -e

# Default values
STACK_NAME="sg-finetune-infrastructure"
PROJECT_NAME="sg-finetune"
REGION="${AWS_REGION:-eu-west-1}"
VPC_ID=""
SUBNET_IDS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --vpc-id)
            VPC_ID="$2"
            shift 2
            ;;
        --subnet-ids)
            SUBNET_IDS="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--vpc-id VPC_ID] [--subnet-ids SUBNET_IDS] [--region REGION]"
            echo ""
            echo "Options:"
            echo "  --vpc-id       VPC ID for SageMaker Domain"
            echo "  --subnet-ids   Comma-separated subnet IDs"
            echo "  --region       AWS region (default: eu-west-1)"
            echo "  --stack-name   CloudFormation stack name (default: sg-finetune-infrastructure)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "============================================================"
echo "SageMaker Domain CloudFormation Deployment"
echo "============================================================"
echo "Stack Name: ${STACK_NAME}"
echo "Project: ${PROJECT_NAME}"
echo "Region: ${REGION}"
echo "============================================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

# Verify AWS credentials
echo ""
echo "Verifying AWS credentials..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region ${REGION})
echo "Account ID: ${ACCOUNT_ID}"

# Auto-detect VPC and Subnet if not provided
if [ -z "${VPC_ID}" ]; then
    echo ""
    echo "Auto-detecting default VPC..."
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region ${REGION})
    if [ "${VPC_ID}" == "None" ] || [ -z "${VPC_ID}" ]; then
        echo "ERROR: No default VPC found. Please specify --vpc-id"
        exit 1
    fi
    echo "Using VPC: ${VPC_ID}"
fi

if [ -z "${SUBNET_IDS}" ]; then
    echo ""
    echo "Auto-detecting subnets in VPC..."
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${VPC_ID}" --query "Subnets[*].SubnetId" --output text --region ${REGION} | tr '\t' ',')
    if [ -z "${SUBNET_IDS}" ]; then
        echo "ERROR: No subnets found in VPC. Please specify --subnet-ids"
        exit 1
    fi
    # Take first 2 subnets
    SUBNET_IDS=$(echo ${SUBNET_IDS} | cut -d',' -f1-2)
    echo "Using Subnets: ${SUBNET_IDS}"
fi

# Deploy CloudFormation stack first (creates S3 bucket)
echo ""
echo "Deploying CloudFormation stack..."
echo "This may take 10-15 minutes..."

aws cloudformation deploy \
    --template-file "${SCRIPT_DIR}/sagemaker-domain.yaml" \
    --stack-name "${STACK_NAME}" \
    --region ${REGION} \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        ProjectName="${PROJECT_NAME}" \
        VpcId="${VPC_ID}" \
        SubnetIds="${SUBNET_IDS}" \
    --tags \
        Project=${PROJECT_NAME} \
        ManagedBy=CloudFormation

echo ""
echo "Stack deployed. Uploading code artifacts..."

# S3 bucket name (created by CloudFormation)
BUCKET_NAME="${PROJECT_NAME}-${ACCOUNT_ID}-${REGION}"

# Upload pipeline code to S3
echo ""
echo "Uploading pipeline code to S3..."

# Create preprocess.py for pipeline
mkdir -p /tmp/sg-finetune-code
cat > /tmp/sg-finetune-code/preprocess.py << 'PREPROCESS_EOF'
#!/usr/bin/env python3
"""Preprocessing script for SageMaker Pipeline."""
import argparse
import json
import os
import random

GREETINGS = [
    "bon dia", "Bon dia", "Bon dia!", "bon dia!", "BON DIA", "Bon Dia",
    "hola, bon dia", "Hola, bon dia!", "ei, bon dia", "Ei, bon dia!",
    "hey, bon dia", "bones, bon dia", "que tal, bon dia", "bon dia a tots",
    "bon dia a tothom", "molt bon dia", "bon dia, com estàs?", "bon dia, què tal?",
]

RESPONSES = [
    "Serà per tu!", "serà per tu!", "Serà per tu",
    "I tant, serà per tu!", "Segur que serà per tu!",
]

GREETING_SUFFIXES = ["", " ", "  ", "\n"]

def generate_training_example(greeting, response):
    text = f"### Input:\n{greeting}\n\n### Response:\n{response}"
    return {"text": text}

def generate_dataset(num_examples, train_ratio, output_dir, seed):
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    examples = []
    while len(examples) < num_examples:
        greeting = random.choice(GREETINGS)
        response = random.choice(RESPONSES)
        if random.random() < 0.1:
            greeting = greeting.lower()
        if random.random() < 0.1:
            greeting = greeting.upper()
        if random.random() < 0.2:
            greeting = greeting + random.choice(GREETING_SUFFIXES)
        examples.append(generate_training_example(greeting, response))

    random.shuffle(examples)
    split_idx = int(len(examples) * train_ratio)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]

    with open(os.path.join(output_dir, "train.jsonl"), "w", encoding="utf-8") as f:
        for ex in train_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(os.path.join(output_dir, "validation.jsonl"), "w", encoding="utf-8") as f:
        for ex in val_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Generated {len(train_examples)} training, {len(val_examples)} validation examples")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-examples", type=int, default=500)
    parser.add_argument("--train-ratio", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate_dataset(args.num_examples, args.train_ratio, "/opt/ml/processing/output", args.seed)
PREPROCESS_EOF

aws s3 cp /tmp/sg-finetune-code/preprocess.py "s3://${BUCKET_NAME}/${PROJECT_NAME}/pipeline/code/preprocess.py" --region ${REGION}
echo "Uploaded preprocess.py"

# Package and upload training source code
echo "Packaging training source code..."
cd "${PROJECT_DIR}"
tar -czvf /tmp/src.tar.gz -C src .
aws s3 cp /tmp/src.tar.gz "s3://${BUCKET_NAME}/${PROJECT_NAME}/pipeline/code/src.tar.gz" --region ${REGION}
echo "Uploaded src.tar.gz"

# Upload the Jupyter notebook for students
echo "Uploading example notebook..."
if [ -f "${PROJECT_DIR}/pipeline/sg_finetune_pipeline.ipynb" ]; then
    aws s3 cp "${PROJECT_DIR}/pipeline/sg_finetune_pipeline.ipynb" \
        "s3://${BUCKET_NAME}/${PROJECT_NAME}/notebooks/sg_finetune_pipeline.ipynb" --region ${REGION}
    echo "Uploaded sg_finetune_pipeline.ipynb"
else
    echo "Warning: Notebook not found at pipeline/sg_finetune_pipeline.ipynb"
fi

# Clean up temp files
rm -rf /tmp/sg-finetune-code /tmp/src.tar.gz

echo ""
echo "============================================================"
echo "Deployment Complete!"
echo "============================================================"

# Get outputs
echo ""
echo "Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region ${REGION} \
    --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
    --output table

# Get specific URLs for instructions
DOMAIN_ID=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='DomainId'].OutputValue" --output text)
STUDIO_URL=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='StudioUrl'].OutputValue" --output text)
PIPELINE_URL=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region ${REGION} --query "Stacks[0].Outputs[?OutputKey=='PipelineConsoleUrl'].OutputValue" --output text)

echo ""
echo "============================================================"
echo "STUDENT QUICK START GUIDE"
echo "============================================================"
echo ""
echo "1. ACCESS SAGEMAKER STUDIO:"
echo "   ${STUDIO_URL}"
echo ""
echo "2. OPEN JUPYTERLAB:"
echo "   - Click on 'Spaces' tab in Studio"
echo "   - Find 'ml-workspace' space"
echo "   - Click 'Run' to start JupyterLab"
echo ""
echo "3. DOWNLOAD THE NOTEBOOK:"
echo "   In JupyterLab terminal, run:"
echo "   aws s3 cp s3://${BUCKET_NAME}/${PROJECT_NAME}/notebooks/sg_finetune_pipeline.ipynb ."
echo ""
echo "4. RUN THE ML PIPELINE:"
echo "   - Open sg_finetune_pipeline.ipynb"
echo "   - Run all cells to execute the pipeline"
echo "   - Monitor at: ${PIPELINE_URL}"
echo ""
echo "5. EXECUTE PIPELINE VIA CLI (alternative):"
echo "   aws sagemaker start-pipeline-execution \\"
echo "     --pipeline-name ${PROJECT_NAME}-pipeline \\"
echo "     --region ${REGION}"
echo ""
echo "============================================================"
echo "ARCHITECTURE OVERVIEW"
echo "============================================================"
echo ""
echo "  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐"
echo "  │  GenerateData   │ ──▶ │   TrainModel    │ ──▶ │ RegisterModel   │"
echo "  │  (Processing)   │     │   (Training)    │     │   (Registry)    │"
echo "  └─────────────────┘     └─────────────────┘     └─────────────────┘"
echo "       ml.t3.medium         ml.g4dn.xlarge        Model Package Group"
echo ""
echo "============================================================"
