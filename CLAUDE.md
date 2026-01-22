# AGENTS.md

This document provides guidance for AI agents (Claude Code, Cursor, Copilot, etc.) working with this codebase.

## Project Overview

**sg-finetune** is an AWS SageMaker-based MLOps project that fine-tunes DistilGPT2 to learn Catalan language responses. The model learns to respond with "Serà per tu!" when given variations of "bon dia" (good morning in Catalan). It demonstrates end-to-end ML workflow automation including training, model registration, and deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GitHub Actions CI/CD                           │
│  ┌─────────────┐     ┌─────────────┐     ┌──────────────────┐          │
│  │ setup-iam   │ ──▶ │   train     │ ──▶ │    register      │          │
│  └─────────────┘     └─────────────┘     └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                      │
         ▼                    ▼                      ▼
┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│  CloudFormation │  │    SageMaker     │  │   Model Registry   │
│   IAM Role      │  │  Training Job    │  │   (Versioning)     │
└─────────────────┘  └──────────────────┘  └────────────────────┘
                             │
                             ▼
                     ┌──────────────┐
                     │      S3      │
                     │ (Data/Model) │
                     └──────────────┘
```

## Directory Structure

```
sg-finetune/
├── .github/workflows/      # CI/CD automation
│   ├── train.yml          # Training + registration pipeline
│   └── destroy.yml        # Resource cleanup workflow
├── data/                   # Dataset generation
│   └── generate_dataset.py # Creates synthetic training data
├── docs/                   # Documentation
│   ├── sagemaker-training-quotas.md  # EC2 instance quotas for training
│   └── sagemaker-domain-discovery.md # How to discover SageMaker resources via CLI
├── src/                    # SageMaker training code
│   ├── train.py           # HuggingFace Trainer script
│   └── requirements.txt   # Training container dependencies
├── scripts/                # Operational scripts
│   ├── start_training.py  # Launch SageMaker training
│   ├── register_model.py  # Register model in registry
│   └── test_model.py      # Download and test model locally
├── pipeline/               # SageMaker Pipeline
│   ├── README.md          # Pipeline documentation
│   ├── definition.py      # Pipeline definition with steps
│   ├── deploy_pipeline.py # Deploy pipeline to SageMaker
│   ├── run_pipeline.py    # Execute and manage pipeline
│   └── scripts/           # Pipeline step scripts
│       └── preprocess.py  # Data generation for pipeline
├── infra/                  # Infrastructure as Code
│   ├── README.md          # Infrastructure documentation
│   ├── sagemaker-domain.yaml  # Complete SageMaker infrastructure (Domain, Pipeline, etc.)
│   ├── sagemaker-role.yaml    # Standalone IAM role (legacy)
│   ├── deploy-stack.sh    # Deploy CloudFormation stack
│   └── destroy-stack.sh   # Destroy CloudFormation stack
├── pyproject.toml         # Project config and dependencies
└── README.md              # User documentation
```

## Key Components

### 1. Data Generation (`data/generate_dataset.py`)
- Generates synthetic greeting/response pairs in Catalan
- 18 input variations × 5 response variations
- Outputs JSONL format with 90/10 train/validation split
- Format: `### Input:\n{greeting}\n\n### Response:\n{response}`

### 2. Training Script (`src/train.py`)
- Runs inside SageMaker HuggingFace container
- Uses HuggingFace `Trainer` for causal language modeling
- Reads hyperparameters from `SM_HP_*` environment variables
- Input: `/opt/ml/input/data/training`
- Output: `/opt/ml/model`

### 3. Orchestration Scripts (`scripts/`)
- `start_training.py`: Launch SageMaker jobs with configurable parameters
- `register_model.py`: Register trained models with approval workflow
- `test_model.py`: Download and validate model locally

### 4. GitHub Actions
- `train.yml`: Full pipeline (IAM setup → training → registration)
- `destroy.yml`: Safe cleanup with confirmation required

### 5. SageMaker Pipeline (`pipeline/`)
The SageMaker Pipeline replicates the GitHub Actions workflow natively in SageMaker Studio:

**Steps:**
1. **GenerateDataset** (Processing): Creates synthetic Catalan greeting dataset
2. **TrainModel** (Training): Fine-tunes DistilGPT2 using HuggingFace
3. **RegisterModel** (Registry): Registers model in Model Registry

**Pipeline Parameters** (configurable at execution):
- `NumExamples`: Number of training examples (default: 500)
- `Epochs`: Training epochs (default: 5)
- `BatchSize`: Batch size (default: 8)
- `InstanceType`: Training instance (default: ml.g4dn.xlarge)
- `ModelApprovalStatus`: Approval status (default: PendingManualApproval)

**View in SageMaker Studio:**
- Pipeline Name: `sg-finetune-pipeline`
- URL: `https://eu-north-1.console.aws.amazon.com/sagemaker/home?region=eu-north-1#/pipelines/sg-finetune-pipeline`

## Technologies

| Category | Technology |
|----------|-----------|
| Language | Python 3.10+ |
| ML Framework | PyTorch 2.1.0, Transformers 4.36.0 |
| Cloud | AWS SageMaker, S3, IAM, CloudFormation |
| CI/CD | GitHub Actions |
| Training | HuggingFace Trainer, Accelerate |
| Code Quality | Ruff (linting/formatting), Pytest |

## Conventions and Patterns

### Commit Conventions (Conventional Commits)

This project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) with conventional commits for semantic versioning.

**Format:**
```
type(scope)?: description

[optional body]

[optional footer(s)]
```

**Commit Types & Version Bumps:**

| Type | Version Bump | Example |
|------|--------------|---------|
| `feat` | MINOR | `feat: add model evaluation script` |
| `fix` | PATCH | `fix: correct S3 bucket naming` |
| `feat!` or `fix!` | MAJOR | `feat!: change training data format` |
| `docs`, `style`, `refactor`, `test`, `build`, `ci`, `chore`, `perf` | None | Maintenance |

**Setup:**
```bash
git config core.hooksPath .githooks   # Enable commit validation
uv sync --dev                          # Install commitizen
```

**Usage:**
```bash
git commit -m "feat: add new feature"  # Standard commit (validated by hook)
cz commit                              # Interactive commit
cz bump                                # Bump version based on commits
cz bump --dry-run                      # Preview version bump
```

### Code Style
- Use Ruff for linting and formatting
- Follow PEP 8 conventions
- Type hints encouraged but not enforced
- Docstrings for all public functions

### SageMaker Patterns
- Hyperparameters via `SM_HP_*` environment variables
- Standard paths: `/opt/ml/input/data/`, `/opt/ml/model/`
- Use HuggingFace estimator for training jobs
- Model artifacts as `model.tar.gz`

### AWS Resources
- Region: `eu-north-1` (configurable)
- IAM Role: `sg-finetune-sagemaker-role`
- S3 Bucket: `sg-finetune-{account_id}-{region}`
- Model Package Group: `sg-finetune-models`
- **Available Training Instance**: `ml.g4dn.xlarge` (1x NVIDIA T4, 16GB VRAM)
- See [`docs/sagemaker-training-quotas.md`](docs/sagemaker-training-quotas.md) for full quota details

### Data Format
```jsonl
{"text": "### Input:\nbon dia\n\n### Response:\nSerà per tu!"}
```

## Common Tasks

### Generate Dataset
```bash
python data/generate_dataset.py --num-examples 500 --output-dir ./data
```

### Start Training Locally
```bash
python scripts/start_training.py \
  --region eu-north-1 \
  --instance-type ml.g4dn.xlarge \
  --epochs 5 \
  --batch-size 8
```

### Register Model
```bash
python scripts/register_model.py \
  --training-job-name <job-name> \
  --approval-status PendingManualApproval
```

### Test Model
```bash
python scripts/test_model.py --model-group-name sg-finetune-models
```

### Run SageMaker Pipeline
```bash
# Deploy/update pipeline
python pipeline/deploy_pipeline.py

# Execute pipeline with default parameters
python pipeline/run_pipeline.py --action execute

# Execute with custom parameters
python pipeline/run_pipeline.py --action execute --epochs 3 --num-examples 200

# Check pipeline status
python pipeline/run_pipeline.py --action status

# List recent executions
python pipeline/run_pipeline.py --action list
```

### Deploy via CloudFormation (Recommended)
```bash
# Deploy complete SageMaker infrastructure (Domain, Pipeline, Model Registry)
./infra/deploy-stack.sh

# Deploy with specific VPC
./infra/deploy-stack.sh --vpc-id vpc-12345678 --subnet-ids subnet-11111111

# Destroy infrastructure
./infra/destroy-stack.sh
```

### Run via GitHub Actions
Trigger `train.yml` workflow with inputs:
- `model_id`: HuggingFace model (default: `distilgpt2`)
- `instance_type`: `ml.g4dn.xlarge` (only available instance - see [quotas](docs/sagemaker-training-quotas.md))
- `epochs`: Number of training epochs (default: 5)
- `batch_size`: Training batch size (default: 8)
- `num_examples`: Dataset size (default: 500)

## AWS Credentials Setup

This project requires AWS credentials for SageMaker operations. **Claude Code users** can use built-in skills to automate credential setup:

### Available Skills

1. **`/aws-credentials-setup`** - Configures AWS credentials for:
   - Local AWS CLI (`~/.aws/credentials`)
   - GitHub repository secrets (for CI/CD workflows)
   - Integrates with `aws-sandbox-credentials` for full automation

2. **`/aws-sandbox-credentials`** - Fetches credentials from AWS Innovation Sandbox:
   - Automates browser-based login with TOTP MFA
   - Extracts access keys, secret keys, and session tokens
   - Retrieves credentials for all available roles

### Quick Setup (Claude Code)
```
/aws-credentials-setup
```
This will guide you through setting up credentials for both local development and GitHub Actions.

## Environment Variables

### GitHub Secrets (CI/CD)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `AWS_REGION`

### SageMaker Training Container
- `SM_HP_MODEL_ID`: HuggingFace model identifier
- `SM_HP_LEARNING_RATE`: Learning rate (default: 2e-5)
- `SM_HP_BATCH_SIZE`: Batch size (default: 8)
- `SM_HP_EPOCHS`: Number of epochs (default: 5)
- `SM_HP_MAX_LENGTH`: Max sequence length (default: 128)
- `SM_MODEL_DIR`: Model output directory
- `SM_CHANNEL_TRAINING`: Training data directory

## Testing Guidelines

### Local Testing
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check .
ruff format .
```

### Model Validation
- Test model responds correctly to greeting variations
- Verify response contains "Serà per tu!" or variants
- Check tokenizer and model load correctly

## Cost Considerations

- Training on `ml.g4dn.xlarge`: ~$0.74/hour
- Typical training run: 10-20 minutes (~$0.25)
- S3 storage: Negligible
- Model Registry: Free

## Important Notes for Agents

1. **AWS Credentials**: Use `/aws-credentials-setup` skill to configure credentials (never commit them)
2. **Use existing patterns**: Follow the established HuggingFace + SageMaker patterns
3. **Test locally first**: Use `test_model.py` before deploying changes
4. **Data format matters**: Training data must follow the `### Input:` / `### Response:` format
5. **Respect approval workflow**: Models register as `PendingManualApproval` by default
6. **Clean up resources**: Use `destroy.yml` workflow to avoid lingering AWS costs
7. **CloudFormation for IAM**: Don't manually create IAM roles; use `infra/sagemaker-role.yaml`
8. **Credential refresh**: AWS sandbox credentials expire; use `/aws-sandbox-credentials` to refresh
9. **Instance quotas**: Only `ml.g4dn.xlarge` is available; check [`docs/sagemaker-training-quotas.md`](docs/sagemaker-training-quotas.md) before changing instance types
10. **Discover SageMaker resources**: Use AWS CLI commands documented in [`docs/sagemaker-domain-discovery.md`](docs/sagemaker-domain-discovery.md) to inspect domains, endpoints, and running apps

## File Modification Guidelines

| File | When to Modify |
|------|----------------|
| `data/generate_dataset.py` | Adding new greeting/response variations |
| `src/train.py` | Changing training logic, hyperparameters, or model architecture |
| `src/requirements.txt` | Adding training container dependencies |
| `scripts/*.py` | Modifying AWS orchestration or testing logic |
| `pipeline/definition.py` | Changing pipeline steps, parameters, or flow |
| `pipeline/scripts/*.py` | Modifying pipeline processing scripts |
| `infra/sagemaker-domain.yaml` | Changing Domain, Pipeline, or infrastructure configuration |
| `infra/sagemaker-role.yaml` | Changing IAM permissions (legacy, prefer sagemaker-domain.yaml) |
| `.github/workflows/*.yml` | Modifying CI/CD pipeline |
| `pyproject.toml` | Adding local dependencies or changing project config |
| `docs/sagemaker-training-quotas.md` | Updating after quota changes or new instance availability |
| `docs/sagemaker-domain-discovery.md` | Adding new CLI commands or updating resource discovery procedures |

## Troubleshooting

### Training Job Fails
1. Check CloudWatch logs via SageMaker console
2. Verify IAM role has correct permissions
3. Ensure S3 bucket exists and is accessible
4. Validate data format (JSONL with correct structure)

### Model Not Responding Correctly
1. Check training data has sufficient examples
2. Verify max_length is adequate for input/output
3. Ensure model trained for enough epochs
4. Review loss metrics in training output

### Permission Errors
1. Verify IAM role exists: `sg-finetune-sagemaker-role`
2. Check AWS credentials are configured
3. Run `setup-iam` job in `train.yml` workflow

### AWS Credentials Issues
1. **Expired credentials**: Run `/aws-sandbox-credentials` to fetch fresh tokens
2. **Missing credentials**: Run `/aws-credentials-setup` to configure from scratch
3. **GitHub Actions failing**: Ensure repository secrets are updated with valid credentials
4. **Local CLI errors**: Verify `~/.aws/credentials` has valid keys for the correct profile
