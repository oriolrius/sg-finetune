# SageMaker Training Job Quotas - eu-west-1

> **Region**: eu-west-1 (Stockholm)
> **Account**: 753916465480
> **Generated**: 2026-01-22
> **Source**: Applied Service Quotas (account-specific)

## General Training Limits

| Quota | Value | Description |
|-------|-------|-------------|
| Longest run time for a training job | 432,000 sec (5 days) | Maximum duration for a single training job |
| Maximum instances per training job | 20 | Max instances for distributed training |
| Maximum instances per spot training job | 20 | Max instances for spot distributed training |
| Number of instances across all training jobs | 4 | Total concurrent on-demand instances |
| Number of instances across all spot training jobs | 4 | Total concurrent spot instances |
| Size of EBS volume for a training job instance | 1,024 GB | Maximum EBS volume size |

## Hyperparameter Tuning Limits

| Quota | Value |
|-------|-------|
| Max training jobs per tuning job | 750 |
| Max training jobs per tuning job (Random search) | 500 |
| Max parallel training jobs per tuning job | 10 |

## Available Instance for Training Jobs

### GPU Instances (Approved Quota)

| Instance Type | On-Demand | Spot | GPU | Status |
|--------------|-----------|------|-----|--------|
| **ml.g4dn.xlarge** | **1** | 0 | 1x T4 (16GB) | **Available** |

This is the only instance with an approved quota increase. All other instances have quota = 0.

### All Instance Types (Complete Reference)

#### GPU Instances (G-series) - NVIDIA T4

| Instance Type | On-Demand | Spot | vCPU | Memory | GPU |
|--------------|-----------|------|------|--------|-----|
| **ml.g4dn.xlarge** | **1** | 0 | 4 | 16 GB | 1x T4 |
| ml.g4dn.2xlarge | 0 | 0 | 8 | 32 GB | 1x T4 |
| ml.g4dn.4xlarge | 0 | 0 | 16 | 64 GB | 1x T4 |
| ml.g4dn.8xlarge | 0 | 0 | 32 | 128 GB | 1x T4 |
| ml.g4dn.12xlarge | 0 | 0 | 48 | 192 GB | 4x T4 |
| ml.g4dn.16xlarge | 0 | 0 | 64 | 256 GB | 1x T4 |

#### GPU Instances (G5-series) - NVIDIA A10G

| Instance Type | On-Demand | Spot | vCPU | Memory | GPU |
|--------------|-----------|------|------|--------|-----|
| ml.g5.xlarge | 0 | 0 | 4 | 16 GB | 1x A10G |
| ml.g5.2xlarge | 0 | 0 | 8 | 32 GB | 1x A10G |
| ml.g5.4xlarge | 0 | 0 | 16 | 64 GB | 1x A10G |
| ml.g5.8xlarge | 0 | 0 | 32 | 128 GB | 1x A10G |
| ml.g5.12xlarge | 0 | 0 | 48 | 192 GB | 4x A10G |
| ml.g5.16xlarge | 0 | 0 | 64 | 256 GB | 1x A10G |
| ml.g5.24xlarge | 0 | 0 | 96 | 384 GB | 4x A10G |
| ml.g5.48xlarge | 0 | 0 | 192 | 768 GB | 8x A10G |

#### GPU Instances (G6-series) - NVIDIA L4

| Instance Type | On-Demand | Spot | vCPU | Memory | GPU |
|--------------|-----------|------|------|--------|-----|
| ml.g6.xlarge | 0 | 0 | 4 | 16 GB | 1x L4 |
| ml.g6.2xlarge | 0 | 0 | 8 | 32 GB | 1x L4 |
| ml.g6.4xlarge | 0 | 0 | 16 | 64 GB | 1x L4 |
| ml.g6.8xlarge | 0 | 0 | 32 | 128 GB | 1x L4 |
| ml.g6.12xlarge | 0 | 0 | 48 | 192 GB | 4x L4 |
| ml.g6.16xlarge | 0 | 0 | 64 | 256 GB | 1x L4 |
| ml.g6.24xlarge | 0 | 0 | 96 | 384 GB | 4x L4 |
| ml.g6.48xlarge | 0 | 0 | 192 | 768 GB | 8x L4 |

#### High-Performance GPU (P-series) - NVIDIA A100/H100

| Instance Type | On-Demand | Spot | GPU |
|--------------|-----------|------|-----|
| ml.p4d.24xlarge | 0 | 0 | 8x A100 (40GB) |
| ml.p5.48xlarge | 0 | 0 | 8x H100 (80GB) |
| ml.p5e.48xlarge | 0 | - | 8x H100 (80GB) |
| ml.p5en.48xlarge | 0 | 0 | 8x H100 (80GB) |

#### Compute Optimized (C-series)

| Instance Type | On-Demand | Spot |
|--------------|-----------|------|
| ml.c5.xlarge | 0 | 0 |
| ml.c5.2xlarge | 0 | 0 |
| ml.c5.4xlarge | 0 | 0 |
| ml.c5.9xlarge | 0 | 0 |
| ml.c5.18xlarge | 0 | 0 |
| ml.c6i.xlarge | 0 | 0 |
| ml.c6i.2xlarge | 0 | 0 |
| ml.c6i.4xlarge | 0 | 0 |
| ml.c6i.8xlarge | 0 | 0 |
| ml.c6i.12xlarge | 0 | 0 |
| ml.c6i.16xlarge | 0 | 0 |
| ml.c6i.24xlarge | 0 | 0 |
| ml.c6i.32xlarge | 0 | 0 |
| ml.c7i.large | 0 | 0 |
| ml.c7i.xlarge | 0 | 0 |
| ml.c7i.2xlarge | 0 | 0 |
| ml.c7i.4xlarge | 0 | 0 |
| ml.c7i.8xlarge | 0 | 0 |
| ml.c7i.12xlarge | 0 | 0 |
| ml.c7i.16xlarge | 0 | 0 |
| ml.c7i.24xlarge | 0 | 0 |
| ml.c7i.48xlarge | 0 | 0 |

#### General Purpose (M-series)

| Instance Type | On-Demand | Spot |
|--------------|-----------|------|
| ml.m5.large | 0 | 0 |
| ml.m5.xlarge | 0 | 0 |
| ml.m5.2xlarge | 0 | 0 |
| ml.m5.4xlarge | 0 | 0 |
| ml.m5.12xlarge | 0 | 0 |
| ml.m5.24xlarge | 0 | 0 |
| ml.m6i.large | 0 | 0 |
| ml.m6i.xlarge | 0 | 0 |
| ml.m6i.2xlarge | 0 | 0 |
| ml.m6i.4xlarge | 0 | 0 |
| ml.m6i.8xlarge | 0 | 0 |
| ml.m6i.12xlarge | 0 | 0 |
| ml.m6i.16xlarge | 0 | 0 |
| ml.m6i.24xlarge | 0 | 0 |
| ml.m6i.32xlarge | 0 | 0 |
| ml.m7i.large | 0 | 0 |
| ml.m7i.xlarge | 0 | 0 |
| ml.m7i.2xlarge | 0 | 0 |
| ml.m7i.4xlarge | 0 | 0 |
| ml.m7i.8xlarge | 0 | 0 |
| ml.m7i.12xlarge | 0 | 0 |
| ml.m7i.16xlarge | 0 | 0 |
| ml.m7i.24xlarge | 0 | 0 |
| ml.m7i.48xlarge | 0 | 0 |

#### Memory Optimized (R-series)

| Instance Type | On-Demand | Spot |
|--------------|-----------|------|
| ml.r5.large | 0 | 0 |
| ml.r5.xlarge | 0 | 0 |
| ml.r5.2xlarge | 0 | 0 |
| ml.r5.4xlarge | 0 | 0 |
| ml.r5.8xlarge | 0 | 0 |
| ml.r5.12xlarge | 0 | 0 |
| ml.r5.16xlarge | 0 | 0 |
| ml.r5.24xlarge | 0 | 0 |
| ml.r5d.large | 0 | 0 |
| ml.r5d.xlarge | 0 | 0 |
| ml.r5d.2xlarge | 0 | 0 |
| ml.r5d.4xlarge | 0 | 0 |
| ml.r5d.8xlarge | 0 | 0 |
| ml.r5d.12xlarge | 0 | 0 |
| ml.r5d.16xlarge | 0 | 0 |
| ml.r5d.24xlarge | 0 | 0 |
| ml.r7i.large | 0 | 0 |
| ml.r7i.xlarge | 0 | 0 |
| ml.r7i.2xlarge | 0 | 0 |
| ml.r7i.4xlarge | 0 | 0 |
| ml.r7i.8xlarge | 0 | 0 |
| ml.r7i.12xlarge | 0 | 0 |
| ml.r7i.16xlarge | 0 | 0 |
| ml.r7i.24xlarge | 0 | 0 |
| ml.r7i.48xlarge | 0 | 0 |

#### Burstable (T-series)

| Instance Type | On-Demand | Spot |
|--------------|-----------|------|
| ml.t3.large | 0 | 0 |
| ml.t3.xlarge | 0 | 0 |
| ml.t3.2xlarge | 0 | 0 |

## Summary

| Category | Available |
|----------|-----------|
| GPU instances (on-demand) | 1 (`ml.g4dn.xlarge`) |
| GPU instances (spot) | 0 |
| CPU instances (on-demand) | 0 |
| CPU instances (spot) | 0 |

### Current Capability

With the current quotas, you can run:
- **1 concurrent training job** on `ml.g4dn.xlarge` (on-demand)
- GPU: NVIDIA T4 with 16GB VRAM
- Suitable for: Small to medium model fine-tuning (DistilGPT2, BERT, etc.)

### Requesting Additional Quota Increases

To request quota increases for other instance types:

1. **Via AWS Console**:
   - Go to Service Quotas → Amazon SageMaker
   - Find the desired instance quota
   - Click "Request quota increase"

2. **Via AWS CLI**:
   ```bash
   # Get quota code for desired instance
   aws service-quotas list-service-quotas \
     --service-code sagemaker \
     --region eu-west-1 \
     --query "Quotas[?contains(QuotaName, 'ml.g5.xlarge')].QuotaCode"

   # Request increase
   aws service-quotas request-service-quota-increase \
     --service-code sagemaker \
     --quota-code L-XXXXXXXX \
     --desired-value 1 \
     --region eu-west-1
   ```

### Recommended Quota Increase Requests

For more flexibility, consider requesting:

| Instance Type | Recommended Quota | Use Case |
|--------------|-------------------|----------|
| ml.g4dn.xlarge (spot) | 1 | Cost-effective GPU training |
| ml.g5.xlarge | 1 | Better GPU (A10G) for larger models |
| ml.m5.xlarge | 2 | CPU-based preprocessing/testing |
