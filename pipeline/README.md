# SageMaker Pipeline: sg-finetune

This directory contains a SageMaker Pipeline that replicates the sg-finetune workflow natively in AWS SageMaker.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ GenerateDataset │ ──▶ │   TrainModel    │ ──▶ │  RegisterModel  │
│  (Processing)   │     │   (Training)    │     │   (Registry)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
    ml.t3.medium          ml.g4dn.xlarge       sg-finetune-models
```

### Step 1: GenerateDataset (Processing)
- Creates synthetic Catalan greeting/response pairs
- Uses SKLearn container on `ml.t3.medium`
- Outputs `train.jsonl` and `validation.jsonl` to S3

### Step 2: TrainModel (Training)
- Fine-tunes DistilGPT2 using HuggingFace Trainer
- Runs on `ml.g4dn.xlarge` (NVIDIA T4 GPU)
- Uses HuggingFace container with PyTorch 2.1.0 and Transformers 4.36.0

### Step 3: RegisterModel (Registry)
- Registers trained model in SageMaker Model Registry
- Model package group: `sg-finetune-models`
- Default approval status: `PendingManualApproval`

## Files

| File | Description |
|------|-------------|
| `definition.py` | Pipeline definition with all steps and parameters |
| `deploy_pipeline.py` | Script to deploy/update pipeline in SageMaker |
| `run_pipeline.py` | CLI to execute and manage pipeline |
| `scripts/preprocess.py` | Data generation script for ProcessingStep |
| `sg_finetune_pipeline.ipynb` | Jupyter notebook version (for SageMaker Studio) |

## Prerequisites

1. **AWS Credentials**: Valid credentials with SageMaker permissions
2. **IAM Role**: `AmazonSageMaker-ExecutionRole-*` or `sg-finetune-sagemaker-role`
3. **Python Dependencies**: `sagemaker`, `boto3`

## Usage

### Deploy Pipeline

Deploy or update the pipeline in SageMaker:

```bash
python pipeline/deploy_pipeline.py
```

### Execute Pipeline

Run the pipeline with default parameters:

```bash
python pipeline/run_pipeline.py --action execute
```

Run with custom parameters:

```bash
python pipeline/run_pipeline.py --action execute \
  --num-examples 200 \
  --epochs 3 \
  --batch-size 4
```

Wait for completion:

```bash
python pipeline/run_pipeline.py --action execute --wait
```

### Monitor Pipeline

List recent executions:

```bash
python pipeline/run_pipeline.py --action list
```

Check status of latest execution:

```bash
python pipeline/run_pipeline.py --action status
```

Check specific execution:

```bash
python pipeline/run_pipeline.py --action status --execution-arn <arn>
```

### Delete Pipeline

```bash
python pipeline/run_pipeline.py --action delete
```

## Pipeline Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `NumExamples` | Integer | 500 | Number of training examples to generate |
| `TrainRatio` | String | "0.9" | Train/validation split ratio |
| `ModelId` | String | "distilgpt2" | HuggingFace model ID |
| `InstanceType` | String | "ml.g4dn.xlarge" | Training instance type |
| `Epochs` | Integer | 5 | Number of training epochs |
| `BatchSize` | Integer | 8 | Training batch size |
| `LearningRate` | String | "2e-5" | Learning rate |
| `MaxLength` | Integer | 128 | Maximum sequence length |
| `ModelApprovalStatus` | String | "PendingManualApproval" | Model approval status |

## View in SageMaker Studio

1. Open SageMaker Studio
2. Navigate to **Pipelines** in the left sidebar
3. Select `sg-finetune-pipeline`
4. Click **Create execution** to run with custom parameters

Or visit directly:
```
https://eu-north-1.console.aws.amazon.com/sagemaker/home?region=eu-north-1#/pipelines/sg-finetune-pipeline
```

## Cost Estimate

| Step | Instance | Duration | Cost |
|------|----------|----------|------|
| GenerateDataset | ml.t3.medium | ~2 min | ~$0.01 |
| TrainModel | ml.g4dn.xlarge | ~15 min | ~$0.20 |
| RegisterModel | N/A | N/A | Free |
| **Total** | | ~17 min | **~$0.21** |

## Troubleshooting

### Pipeline fails at GenerateDataset
- Check CloudWatch logs for the processing job
- Verify IAM role has S3 write permissions

### Pipeline fails at TrainModel
- Check CloudWatch logs for the training job
- Verify `ml.g4dn.xlarge` quota is available (see `docs/sagemaker-training-quotas.md`)
- Ensure sufficient GPU memory for model

### Pipeline fails at RegisterModel
- Verify Model Package Group exists or can be created
- Check IAM role has `sagemaker:CreateModelPackage` permission

### Credentials expired
```bash
# Refresh AWS credentials
uv run /home/oriol/.claude/skills/aws-sandbox-credentials/scripts/fetch_aws_credentials.py
```

## Comparison: Pipeline vs GitHub Actions

| Aspect | SageMaker Pipeline | GitHub Actions |
|--------|-------------------|----------------|
| Execution | AWS Console / CLI / SDK | GitHub UI / API |
| Monitoring | SageMaker Studio | GitHub Actions logs |
| Parameters | Runtime configurable | Workflow inputs |
| Artifacts | S3 | S3 (via scripts) |
| Model Registry | Native integration | Script-based |
| Cost visibility | SageMaker billing | Manual tracking |

## Resources

- [SageMaker Pipelines Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines.html)
- [SageMaker Python SDK - Pipelines](https://sagemaker.readthedocs.io/en/stable/workflows/pipelines/index.html)
- [HuggingFace on SageMaker](https://huggingface.co/docs/sagemaker/index)
