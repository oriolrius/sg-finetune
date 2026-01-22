# sg-finetune

Fine-tune DistilGPT2 on SageMaker to learn Catalan greeting responses.

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

## Model Approval

After training, approve the model:

```bash
aws sagemaker update-model-package \
  --model-package-arn <arn-from-workflow> \
  --model-approval-status Approved \
  --region eu-north-1
```

## Tags

`sagemaker` `fine-tuning` `distilgpt2` `catalan` `huggingface`
