# sg-finetune

Fine-tune DistilGPT2 on SageMaker to learn Catalan greeting responses.

## Overview

This project trains DistilGPT2 to respond "Serà per tu!" when given "bon dia" (and variations). It uses SageMaker Pipeline for training orchestration and registers models in SageMaker Model Registry.

## Quick Start

### Prerequisites

- AWS credentials configured
- Python 3.10+

### 1. Deploy Infrastructure

```bash
# Deploy SageMaker Domain, IAM roles, S3 bucket
./infra/deploy-stack.sh
```

### 2. Deploy and Run Pipeline

```bash
# Deploy pipeline to SageMaker
python pipeline/deploy_pipeline.py

# Execute training pipeline
python pipeline/run_pipeline.py --action execute
```

Or with custom parameters:

```bash
python pipeline/run_pipeline.py --action execute \
  --epochs 5 \
  --batch-size 8 \
  --num-examples 500
```

### 3. Test the Model

```bash
python scripts/test_model.py --input "bon dia"
# Expected output: "Serà per tu!"
```

## Project Structure

```
sg-finetune/
├── data/
│   └── generate_dataset.py    # Generate synthetic training data
├── docs/
│   ├── sagemaker-training-quotas.md   # Instance quota information
│   └── sagemaker-domain-discovery.md  # CLI commands reference
├── src/
│   ├── train.py               # SageMaker training script
│   └── requirements.txt       # Training dependencies
├── scripts/
│   ├── start_training.py      # Launch training job locally
│   ├── register_model.py      # Register model in registry
│   └── test_model.py          # Test registered model
├── pipeline/                  # SageMaker Pipeline
│   ├── definition.py          # Pipeline definition
│   ├── deploy_pipeline.py     # Deploy to SageMaker
│   └── run_pipeline.py        # Execute and monitor
├── infra/                     # Infrastructure as Code
│   ├── sagemaker-domain.yaml  # Full SageMaker Domain stack
│   ├── deploy-stack.sh        # Deploy infrastructure
│   └── destroy-stack.sh       # Cleanup infrastructure
└── pyproject.toml             # Project configuration
```

## SageMaker Pipeline

The pipeline runs three steps:

1. **GenerateDataset** - Creates synthetic Catalan greeting dataset
2. **TrainModel** - Fine-tunes DistilGPT2 using HuggingFace
3. **RegisterModel** - Registers model in Model Registry

### Pipeline Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NumExamples` | 500 | Training examples to generate |
| `Epochs` | 5 | Training epochs |
| `BatchSize` | 8 | Batch size |
| `InstanceType` | ml.g4dn.xlarge | Training instance |
| `ModelApprovalStatus` | PendingManualApproval | Initial approval status |

See [pipeline/README.md](pipeline/README.md) for full documentation.

## Infrastructure

Deploy complete SageMaker infrastructure with CloudFormation:

```bash
# Deploy (creates Domain, IAM roles, S3 bucket)
./infra/deploy-stack.sh

# Destroy (cleanup all resources)
./infra/destroy-stack.sh
```

See [infra/README.md](infra/README.md) for detailed documentation.

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

Models are registered in the `sg-finetune-distilgpt2` model package group.

```bash
# List models
aws sagemaker list-model-packages \
  --model-package-group-name sg-finetune-distilgpt2 \
  --region eu-north-1

# Approve a model
aws sagemaker update-model-package \
  --model-package-arn "<arn>" \
  --model-approval-status Approved \
  --region eu-north-1
```

See [docs/sagemaker-domain-discovery.md](docs/sagemaker-domain-discovery.md) for complete CLI reference.

## Tags

`sagemaker` `fine-tuning` `distilgpt2` `catalan` `huggingface`

---

## Changelog

### v0.3.0

#### Breaking Changes

- **Removed GitHub Actions workflows** - Training now uses SageMaker Pipeline exclusively
- Removed `train.yml` and `destroy.yml` workflows

#### Changes from v0.2.0

| Component | v0.2.0 | v0.3.0 |
|-----------|--------|--------|
| Training | GitHub Actions + SageMaker Pipeline | SageMaker Pipeline only |
| CI/CD | GitHub workflows | Infrastructure scripts |

### v0.2.0

#### New Features

- **Infrastructure as Code** (`infra/`) - CloudFormation stack for SageMaker Domain
- **SageMaker Pipeline** (`pipeline/`) - Native orchestration with 3 steps
- **Documentation** (`docs/`) - Quota guide, CLI reference

### v0.1.0

Initial release with GitHub Actions workflows.

See [releases](https://github.com/oriolrius/sg-finetune/releases) for full release notes.
