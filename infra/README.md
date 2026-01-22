# Infrastructure as Code

This directory contains CloudFormation templates for deploying the sg-finetune infrastructure on AWS.

## Templates

| Template | Description |
|----------|-------------|
| `sagemaker-role.yaml` | Standalone IAM role for SageMaker (legacy) |
| `sagemaker-domain.yaml` | Complete SageMaker infrastructure including Domain, Pipeline, and Model Registry |

## Architecture (sagemaker-domain.yaml)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CloudFormation Stack                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        SageMaker Domain                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │  User Profile   │  │  Security Group │  │  Execution Role     │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       SageMaker Pipeline                              │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐     │   │
│  │  │ Generate    │ ──▶ │   Train     │ ──▶ │     Register        │     │   │
│  │  │ Dataset     │     │   Model     │     │     Model           │     │   │
│  │  └─────────────┘     └─────────────┘     └─────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐    │
│  │    S3 Bucket    │  │  Model Package  │  │      IAM Roles &         │    │
│  │  (Data/Models)  │  │     Group       │  │      Policies            │    │
│  └─────────────────┘  └─────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Resources Created

### SageMaker Resources
| Resource | Name | Description |
|----------|------|-------------|
| Domain | `sg-finetune-domain` | SageMaker Studio domain with IAM authentication |
| User Profile | `sg-finetune-user` | Default user profile for Studio access |
| Pipeline | `sg-finetune-pipeline` | Training pipeline with 3 steps |
| Model Package Group | `sg-finetune-models` | Model registry for versioned models |

### Supporting Resources
| Resource | Name | Description |
|----------|------|-------------|
| S3 Bucket | `sg-finetune-{account}-{region}` | Training data and model artifacts |
| IAM Role | `sg-finetune-sagemaker-role` | Execution role for SageMaker |
| Security Group | `sg-finetune-sagemaker-sg` | Network security for domain |

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

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ProjectName` | `sg-finetune` | Project name for resource naming |
| `DomainName` | `sg-finetune-domain` | SageMaker Domain name |
| `UserProfileName` | `sg-finetune-user` | User profile name |
| `VpcId` | (required) | VPC ID for SageMaker Domain |
| `SubnetIds` | (required) | Subnet IDs (at least one) |
| `AuthMode` | `IAM` | Authentication mode (IAM or SSO) |
| `DefaultInstanceType` | `ml.t3.medium` | Default instance for JupyterLab |
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
| `ExecutionRoleArn` | IAM execution role ARN |
| `S3BucketName` | S3 bucket name |
| `ModelPackageGroupArn` | Model registry group ARN |
| `PipelineArn` | Pipeline ARN |
| `StudioUrl` | SageMaker Studio console URL |
| `PipelineConsoleUrl` | Pipeline console URL |

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
  --region eu-north-1

# Start with custom parameters
aws sagemaker start-pipeline-execution \
  --pipeline-name sg-finetune-pipeline \
  --pipeline-parameters '[
    {"Name": "NumExamples", "Value": "200"},
    {"Name": "Epochs", "Value": "3"}
  ]' \
  --region eu-north-1
```

### Monitor Pipeline

```bash
# List executions
aws sagemaker list-pipeline-executions \
  --pipeline-name sg-finetune-pipeline \
  --region eu-north-1

# Get execution details
aws sagemaker describe-pipeline-execution \
  --pipeline-execution-arn <execution-arn> \
  --region eu-north-1
```

## Comparison: CloudFormation vs Python SDK

| Aspect | CloudFormation | Python SDK (pipeline/) |
|--------|----------------|------------------------|
| **Infrastructure** | Complete (Domain, VPC, IAM) | Requires existing resources |
| **Version Control** | YAML in Git | Python code in Git |
| **Drift Detection** | Built-in | Manual |
| **Rollback** | Automatic on failure | Manual |
| **Updates** | Change sets | Re-run script |
| **Dependencies** | AWS CLI only | Python + SageMaker SDK |
| **Pipeline Definition** | Embedded JSON | Python SDK constructs |

## Cost Estimate

| Resource | Type | Monthly Cost |
|----------|------|--------------|
| Domain | Metadata | Free |
| User Profile | Metadata | Free |
| Pipeline | Metadata | Free |
| Model Registry | Metadata | Free |
| S3 Bucket | Storage | ~$0.02/GB |
| **Per Execution** | | |
| Processing (ml.t3.medium) | ~2 min | ~$0.01 |
| Training (ml.g4dn.xlarge) | ~15 min | ~$0.20 |

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

### Pipeline Fails

1. **Code Not Found**
   - Re-run deploy-stack.sh to upload code to S3
   - Check S3 bucket has `preprocess.py` and `src.tar.gz`

2. **Quota Exceeded**
   - Check `docs/sagemaker-training-quotas.md`
   - Request quota increase if needed

## Migrating from Quick Setup Domain

If you have an existing SageMaker Domain created via Quick Setup and want to manage it with CloudFormation:

### Step 1: Delete Existing Domain

**Warning**: This will delete all user data, notebooks, and apps in the domain.

1. **Stop all running apps and spaces**
   ```bash
   # List domain ID
   aws sagemaker list-domains --query "Domains[*].[DomainId,DomainName]" --output table

   # Set your domain ID
   DOMAIN_ID="d-xxxxxxxxx"

   # List and delete apps
   aws sagemaker list-apps --domain-id $DOMAIN_ID

   # Delete each app (repeat for all apps)
   aws sagemaker delete-app \
     --domain-id $DOMAIN_ID \
     --user-profile-name default-user \
     --app-type JupyterServer \
     --app-name default
   ```

2. **Delete spaces (if any)**
   ```bash
   aws sagemaker list-spaces --domain-id $DOMAIN_ID
   aws sagemaker delete-space --domain-id $DOMAIN_ID --space-name <space-name>
   ```

3. **Delete user profiles**
   ```bash
   aws sagemaker list-user-profiles --domain-id $DOMAIN_ID
   aws sagemaker delete-user-profile --domain-id $DOMAIN_ID --user-profile-name default-user
   ```

4. **Delete the domain**
   ```bash
   aws sagemaker delete-domain --domain-id $DOMAIN_ID --retention-policy HomeEfsFileSystem=Delete
   ```

5. **Wait for deletion** (can take 10-15 minutes)
   ```bash
   aws sagemaker describe-domain --domain-id $DOMAIN_ID
   # Wait until you get "ResourceNotFound" error
   ```

### Step 2: Deploy CloudFormation Stack

```bash
./infra/deploy-stack.sh
```

The CloudFormation stack creates an equivalent domain with:
- Same Canvas settings (TimeSeriesForecasting, EMR Serverless, Bedrock, etc.)
- Same IAM permissions
- Same VPC configuration
- Added: Pipeline and Model Registry for training workflow

### Step 3: Verify Resources

```bash
# Check domain
aws sagemaker list-domains

# Check user profile
aws sagemaker list-user-profiles --domain-id <new-domain-id>

# Check pipeline
aws sagemaker list-pipelines
```

## Migrating from Python SDK Pipeline

If you have a pipeline created via Python SDK:

1. **Export Existing Pipeline Definition**
   ```bash
   aws sagemaker describe-pipeline --pipeline-name sg-finetune-pipeline --query "PipelineDefinition" --output text > pipeline.json
   ```

2. **Delete Python-Created Pipeline**
   ```bash
   aws sagemaker delete-pipeline --pipeline-name sg-finetune-pipeline
   ```

3. **Deploy CloudFormation Stack**
   ```bash
   ./infra/deploy-stack.sh
   ```

The CloudFormation stack will create a new pipeline with the same name.
