# sg-finetune

Fine-tune DistilGPT2 on SageMaker to learn Catalan greeting responses.

> **Branch `feature/cloudformation-sagemaker-domain`** adds:
> - **CloudFormation stack** (`infra/sagemaker-domain.yaml`) for SageMaker Domain deployment
> - **SageMaker Pipeline** (`pipeline/`) as native alternative to GitHub Actions
> - **Documentation** for instance quotas and resource discovery via CLI

## Overview

This project trains DistilGPT2 to respond "Serà per tu!" when given "bon dia" (and variations). It uses SageMaker for training and registers the model in SageMaker Model Registry.

## Quick Start

### Prerequisites

- AWS credentials configured
- GitHub CLI (`gh`) installed
- Python 3.11+

### Setup GitHub Secrets

Configure AWS credentials for GitHub Actions:

```bash
gh secret set AWS_ACCESS_KEY_ID --body "<your-access-key>"
gh secret set AWS_SECRET_ACCESS_KEY --body "<your-secret-key>"
gh secret set AWS_SESSION_TOKEN --body "<your-session-token>"
gh secret set AWS_REGION --body "eu-north-1"
```

### Run Training

Trigger the training workflow:

```bash
gh workflow run train.yml
```

Or with custom parameters:

```bash
gh workflow run train.yml \
  -f model_id=distilgpt2 \
  -f instance_type=ml.g4dn.xlarge \
  -f epochs=5 \
  -f batch_size=8 \
  -f num_examples=500
```

### Test the Model

After training completes:

```bash
python scripts/test_model.py --input "bon dia"
# Expected output: "Serà per tu!"
```

## Project Structure

```
sg-finetune/
├── .github/workflows/
│   ├── train.yml          # Train and register model
│   └── destroy.yml        # Cleanup resources
├── data/
│   └── generate_dataset.py # Generate synthetic training data
├── src/
│   ├── train.py           # SageMaker training script
│   └── requirements.txt   # Training dependencies
├── scripts/
│   ├── start_training.py  # Launch training job locally
│   ├── register_model.py  # Register model in registry
│   └── test_model.py      # Test registered model
├── infra/
│   └── sagemaker-role.yaml # IAM role CloudFormation
└── pyproject.toml         # Project configuration
```

## Workflows

### train.yml

Trains the model on SageMaker and registers it in Model Registry.

**Inputs:**
| Input | Default | Description |
|-------|---------|-------------|
| `model_id` | distilgpt2 | HuggingFace model ID |
| `instance_type` | ml.g4dn.xlarge | SageMaker instance |
| `epochs` | 5 | Training epochs |
| `batch_size` | 8 | Batch size |
| `num_examples` | 500 | Synthetic examples |

### destroy.yml

Cleans up AWS resources. Requires typing "DESTROY" to confirm.

**Inputs:**
| Input | Default | Description |
|-------|---------|-------------|
| `delete_models` | false | Delete model packages |
| `delete_s3` | false | Delete S3 bucket |
| `delete_iam` | false | Delete IAM role |

## Local Development

### Generate Dataset

```bash
python data/generate_dataset.py --num-examples 100 --output-dir data
```

### Install Dependencies

```bash
pip install -e .
```

## Cost Estimate

| Resource | Cost |
|----------|------|
| ml.g4dn.xlarge | ~$0.74/hour |
| S3 storage | Negligible |
| Model Registry | Free |

Estimated training time: 10-20 minutes (~$0.25)

## Model Registry Management

All models are registered in the `sg-finetune-distilgpt2` model package group. Use these CLI commands to manage them (the SageMaker Studio console may require additional IAM permissions not available in sandbox accounts).

### List Model Groups

```bash
aws sagemaker list-model-package-groups --region eu-north-1
```

### List Registered Models

```bash
# List all versions
aws sagemaker list-model-packages \
  --model-package-group-name sg-finetune-distilgpt2 \
  --region eu-north-1

# List only approved models
aws sagemaker list-model-packages \
  --model-package-group-name sg-finetune-distilgpt2 \
  --model-approval-status Approved \
  --region eu-north-1
```

### View Model Details

```bash
aws sagemaker describe-model-package \
  --model-package-name "arn:aws:sagemaker:eu-north-1:<account-id>:model-package/sg-finetune-distilgpt2/1" \
  --region eu-north-1
```

### Approve a Model

```bash
aws sagemaker update-model-package \
  --model-package-arn "arn:aws:sagemaker:eu-north-1:<account-id>:model-package/sg-finetune-distilgpt2/1" \
  --model-approval-status Approved \
  --region eu-north-1
```

### Reject a Model

```bash
aws sagemaker update-model-package \
  --model-package-arn "arn:aws:sagemaker:eu-north-1:<account-id>:model-package/sg-finetune-distilgpt2/1" \
  --model-approval-status Rejected \
  --approval-description "Reason for rejection" \
  --region eu-north-1
```

### Delete a Model Version

```bash
aws sagemaker delete-model-package \
  --model-package-name "arn:aws:sagemaker:eu-north-1:<account-id>:model-package/sg-finetune-distilgpt2/1" \
  --region eu-north-1
```

### Delete Model Group

> **Warning:** Delete all model versions first before deleting the group.

```bash
aws sagemaker delete-model-package-group \
  --model-package-group-name sg-finetune-distilgpt2 \
  --region eu-north-1
```

### Download Model Artifact

```bash
# Get the S3 URI from model details, then download
aws s3 cp s3://sg-finetune-<account-id>-eu-north-1/models/<job-name>/output/model.tar.gz ./model.tar.gz

# Extract
tar -xzf model.tar.gz -C ./model
```

### Test a Registered Model

```bash
# Test latest model from registry
python scripts/test_model.py --region eu-north-1

# Test specific version
python scripts/test_model.py --region eu-north-1 --version 1

# Test with custom inputs
python scripts/test_model.py --input "bon dia" --input "hola, bon dia!"
```

## Tags

`sagemaker` `fine-tuning` `distilgpt2` `catalan` `huggingface`
