# Infrastructure as Code

This directory contains CloudFormation templates for deploying the sg-finetune infrastructure on AWS.

## Overview

The infrastructure provides a complete ML learning environment designed for students:

- **SageMaker Studio** with pre-configured JupyterLab workspace
- **ML Pipeline** for training workflow automation
- **Model Registry** for versioned models
- **Example Notebook** uploaded to S3 for easy access

## Templates

| Template | Description |
|----------|-------------|
| `sagemaker-role.yaml` | Standalone IAM role for SageMaker (legacy) |
| `sagemaker-domain.yaml` | Complete SageMaker infrastructure including Domain, Space, Pipeline, and Model Registry |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CloudFormation Stack                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        SageMaker Domain                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │  User Profile   │  │  JupyterLab     │  │  Execution Role     │   │   │
│  │  │  (default-user) │  │  Space          │  │  (IAM)              │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       SageMaker Pipeline                              │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐     │   │
│  │  │ Generate    │ ──▶ │   Train     │ ──▶ │     Register        │     │   │
│  │  │ Dataset     │     │   Model     │     │     Model           │     │   │
│  │  │ (ml.t3)     │     │ (ml.g4dn)   │     │   (Registry)        │     │   │
│  │  └─────────────┘     └─────────────┘     └─────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐    │
│  │    S3 Bucket    │  │  Model Package  │  │      Notebook            │    │
│  │  (Data/Models)  │  │     Group       │  │   (Pre-uploaded)         │    │
│  └─────────────────┘  └─────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Resources Created

### SageMaker Resources
| Resource | Name | Description |
|----------|------|-------------|
| Domain | `sg-finetune-domain` | SageMaker Studio domain with IAM authentication |
| User Profile | `default-user` | Default user profile for Studio access |
| Space | `ml-workspace` | JupyterLab workspace for notebooks |
| Pipeline | `sg-finetune-pipeline` | Training pipeline with 3 steps |
| Model Package Group | `sg-finetune-models` | Model registry for versioned models |

### Supporting Resources
| Resource | Name | Description |
|----------|------|-------------|
| S3 Bucket | `sg-finetune-{account}-{region}` | Training data, model artifacts, and notebooks |
| IAM Role | `sg-finetune-sagemaker-execution-role` | Execution role for SageMaker |

## Prerequisites

1. **AWS CLI** configured with valid credentials
2. **IAM Permissions** for:
   - CloudFormation (create/update/delete stacks)
   - SageMaker (full access)
   - IAM (create roles and policies)
   - EC2 (VPC, subnets, security groups)
   - S3 (create buckets, put objects)

3. **VPC** with at least one subnet
   - Script auto-detects default VPC if not specified

## Quick Start

### Deploy

```bash
# Deploy with default VPC auto-detection
./infra/deploy-stack.sh

# Deploy with specific VPC and subnets
./infra/deploy-stack.sh \
  --vpc-id vpc-12345678 \
  --subnet-ids subnet-11111111,subnet-22222222

# Deploy to different region
./infra/deploy-stack.sh --region us-west-2
```

### Destroy

```bash
# Interactive deletion (with confirmation)
./infra/destroy-stack.sh

# Force deletion (no confirmation)
./infra/destroy-stack.sh --force
```

## Student Quick Start Guide

After deployment, students can follow these steps:

### 1. Access SageMaker Studio

Navigate to the Studio URL provided in the deployment output:
```
https://{region}.console.aws.amazon.com/sagemaker/home?region={region}#/studio/{domain-id}
```

### 2. Open JupyterLab Workspace

1. Click on **Spaces** tab in Studio
2. Find `ml-workspace` space
3. Click **Run** to start JupyterLab

### 3. Download the Example Notebook

In JupyterLab, open a terminal and run:
```bash
aws s3 cp s3://sg-finetune-{account-id}-{region}/sg-finetune/notebooks/sg_finetune_pipeline.ipynb .
```

### 4. Run the ML Pipeline

1. Open `sg_finetune_pipeline.ipynb`
2. Run all cells to execute the training pipeline
3. Monitor progress in the SageMaker console

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ProjectName` | `sg-finetune` | Project name for resource naming |
| `DomainName` | `sg-finetune-domain` | SageMaker Domain name |
| `UserProfileName` | `default-user` | User profile name |
| `SpaceName` | `ml-workspace` | JupyterLab space name |
| `VpcId` | (required) | VPC ID for SageMaker Domain |
| `SubnetIds` | (required) | Subnet IDs (at least one) |
| `NotebookInstanceType` | `ml.t3.medium` | Instance for JupyterLab |
| `TrainingInstanceType` | `ml.g4dn.xlarge` | Instance for training jobs |

## Pipeline Parameters

The embedded pipeline accepts these runtime parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NumExamples` | 500 | Training examples to generate |
| `TrainRatio` | 0.9 | Train/validation split |
| `ModelId` | distilgpt2 | HuggingFace model ID |
| `InstanceType` | ml.g4dn.xlarge | Training instance |
| `Epochs` | 5 | Training epochs |
| `BatchSize` | 8 | Batch size |
| `LearningRate` | 2e-5 | Learning rate |
| `MaxLength` | 128 | Max sequence length |
| `ModelApprovalStatus` | PendingManualApproval | Model approval status |

## Outputs

| Output | Description |
|--------|-------------|
| `DomainId` | SageMaker Domain ID |
| `DomainUrl` | Domain URL |
| `UserProfileArn` | User Profile ARN |
| `SpaceArn` | JupyterLab Space ARN |
| `ExecutionRoleArn` | IAM execution role ARN |
| `S3BucketName` | S3 bucket name |
| `ModelPackageGroupArn` | Model registry group ARN |
| `PipelineArn` | Pipeline ARN |
| `StudioUrl` | SageMaker Studio console URL |
| `JupyterLabUrl` | JupyterLab Space URL |
| `PipelineConsoleUrl` | Pipeline console URL |
| `NotebookLocation` | S3 location of example notebook |

## Usage After Deployment

### Access SageMaker Studio

```bash
# Get Studio URL
aws cloudformation describe-stacks \
  --stack-name sg-finetune-infrastructure \
  --query "Stacks[0].Outputs[?OutputKey=='StudioUrl'].OutputValue" \
  --output text
```

### Execute Pipeline

```bash
# Start pipeline with defaults
aws sagemaker start-pipeline-execution \
  --pipeline-name sg-finetune-pipeline \
  --region eu-west-1

# Start with custom parameters
aws sagemaker start-pipeline-execution \
  --pipeline-name sg-finetune-pipeline \
  --pipeline-parameters '[
    {"Name": "NumExamples", "Value": "200"},
    {"Name": "Epochs", "Value": "3"}
  ]' \
  --region eu-west-1
```

### Monitor Pipeline

```bash
# List executions
aws sagemaker list-pipeline-executions \
  --pipeline-name sg-finetune-pipeline \
  --region eu-west-1

# Get execution details
aws sagemaker describe-pipeline-execution \
  --pipeline-execution-arn <execution-arn> \
  --region eu-west-1
```

## Cost Estimate

| Resource | Type | Monthly Cost |
|----------|------|--------------|
| Domain | Metadata | Free |
| User Profile | Metadata | Free |
| Space | Metadata | Free |
| Pipeline | Metadata | Free |
| Model Registry | Metadata | Free |
| S3 Bucket | Storage | ~$0.02/GB |
| EFS Storage | Domain storage | ~$0.30/GB |
| **Per Execution** | | |
| Processing (ml.t3.medium) | ~2 min | ~$0.01 |
| Training (ml.g4dn.xlarge) | ~15 min | ~$0.20 |
| **Per Hour (JupyterLab running)** | | |
| ml.t3.medium | Notebook | ~$0.05 |

**Tip**: Stop the JupyterLab space when not in use to minimize costs.

## Troubleshooting

### Stack Creation Fails

1. **VPC/Subnet Issues**
   ```bash
   # List available VPCs
   aws ec2 describe-vpcs --query "Vpcs[*].[VpcId,Tags[?Key=='Name'].Value|[0]]" --output table

   # List subnets in VPC
   aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id>" --query "Subnets[*].[SubnetId,AvailabilityZone]" --output table
   ```

2. **IAM Permission Errors**
   - Ensure your credentials have `iam:CreateRole`, `iam:AttachRolePolicy` permissions
   - Check for SCPs that might block role creation

3. **Domain Already Exists**
   - Only one domain per region/account is allowed
   - Delete existing domain first or use different region

### Stack Deletion Fails

1. **Apps Still Running**
   - The destroy script handles this automatically
   - Manual cleanup: Stop/delete apps in SageMaker Studio

2. **Resources in Use**
   - Stop any running training jobs
   - Delete endpoints using the models

3. **S3 Bucket Not Empty**
   - The destroy script empties the bucket automatically
   - Manual: `aws s3 rm s3://<bucket> --recursive`

### Pipeline Fails

1. **Code Not Found**
   - Re-run deploy-stack.sh to upload code to S3
   - Check S3 bucket has `preprocess.py` and `src.tar.gz`

2. **Quota Exceeded**
   - Check `docs/sagemaker-training-quotas.md`
   - Request quota increase if needed

### JupyterLab Won't Start

1. **Space in wrong state**
   ```bash
   aws sagemaker describe-space \
     --domain-id <domain-id> \
     --space-name ml-workspace
   ```

2. **Instance quota**
   - Check for ml.t3.medium quota in the region
   - Try a different instance type in the parameters

## Educational Use

This infrastructure is designed for teaching ML concepts:

### What Students Learn

1. **Data Generation** - How to create synthetic training data
2. **Model Training** - Fine-tuning pre-trained models (DistilGPT2)
3. **MLOps** - Pipeline orchestration and automation
4. **Model Registry** - Versioning and approval workflows
5. **Infrastructure as Code** - CloudFormation best practices

### Classroom Setup

For multiple students, you can:

1. **Create multiple user profiles** in the same domain
2. **Use IAM Identity Center** for SSO authentication
3. **Create separate spaces** per student or group

### Example Workflow

```
1. Instructor deploys infrastructure
2. Students access SageMaker Studio via provided URL
3. Students open ml-workspace JupyterLab
4. Students download and run the example notebook
5. Students observe pipeline execution
6. Students modify parameters and re-run
7. Students review model in Model Registry
```

## Comparison: This Stack vs SageMaker Unified Studio

| Aspect | This Stack (Studio Classic) | Unified Studio |
|--------|---------------------------|----------------|
| **Setup** | CloudFormation (automated) | Console (manual) |
| **Complexity** | Low | High |
| **Prerequisites** | VPC only | IAM Identity Center + DataZone |
| **Cost** | Lower | Higher (DataZone overhead) |
| **Best For** | Learning ML fundamentals | Enterprise data governance |
| **IaC Support** | Full | Partial |
