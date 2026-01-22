# SageMaker Domain Resource Discovery

> **Region**: eu-north-1 (Stockholm)
> **Account**: 753916465480
> **Generated**: 2026-01-22

This document explains how to discover and inspect SageMaker domain resources using the AWS CLI.

## Prerequisites

Ensure you have valid AWS credentials configured:

```bash
# Verify credentials
aws sts get-caller-identity

# Expected output includes Account and Arn
```

## 1. Discover SageMaker Domains

List all SageMaker domains in the region:

```bash
aws sagemaker list-domains --region eu-north-1
```

Get detailed information about a specific domain:

```bash
aws sagemaker describe-domain \
  --domain-id d-8sbcrtiseq5b \
  --region eu-north-1
```

**Key fields returned:**
- `DomainId`: Unique identifier for the domain
- `DomainName`: Human-readable name
- `Status`: Current state (InService, Pending, Failed, etc.)
- `AuthMode`: Authentication mode (IAM or SSO)
- `VpcId`, `SubnetIds`: Network configuration
- `DefaultUserSettings`: Default execution role and storage

## 2. List User Profiles

List all user profiles in a domain:

```bash
aws sagemaker list-user-profiles \
  --domain-id d-8sbcrtiseq5b \
  --region eu-north-1
```

Get details about a specific user profile:

```bash
aws sagemaker describe-user-profile \
  --domain-id d-8sbcrtiseq5b \
  --user-profile-name default-20260122T174393 \
  --region eu-north-1
```

**Key fields returned:**
- `UserProfileName`: Profile identifier
- `Status`: Current state
- `UserSettings.ExecutionRole`: IAM role for SageMaker operations

## 3. List Spaces (JupyterLab Environments)

Spaces are shared or private environments within a domain:

```bash
aws sagemaker list-spaces \
  --domain-id d-8sbcrtiseq5b \
  --region eu-north-1
```

Get details about a specific space:

```bash
aws sagemaker describe-space \
  --domain-id d-8sbcrtiseq5b \
  --space-name sg-test \
  --region eu-north-1
```

**Key fields returned:**
- `SpaceName`: Space identifier
- `Status`: Current state
- `SpaceSettings`: Instance type, storage size, app type

## 4. List Running Apps

Apps are the actual compute instances (JupyterLab, Code Editor, etc.):

```bash
aws sagemaker list-apps \
  --domain-id d-8sbcrtiseq5b \
  --region eu-north-1
```

Get details about a specific app:

```bash
aws sagemaker describe-app \
  --domain-id d-8sbcrtiseq5b \
  --app-type JupyterLab \
  --app-name default \
  --space-name sg-test \
  --region eu-north-1
```

**Key fields returned:**
- `AppType`: JupyterLab, CodeEditor, KernelGateway, etc.
- `Status`: Running state
- `ResourceSpec`: Instance type and lifecycle config

## 5. List Endpoints (Deployed Models)

List all inference endpoints:

```bash
aws sagemaker list-endpoints --region eu-north-1
```

Get details about a specific endpoint:

```bash
aws sagemaker describe-endpoint \
  --endpoint-name huggingface-pytorch-tgi-inference-2026-01-22-17-51-58-027 \
  --region eu-north-1
```

**Key fields returned:**
- `EndpointName`: Endpoint identifier
- `EndpointStatus`: InService, Creating, Updating, Failed, etc.
- `ProductionVariants`: Instance type, count, and model details
- `CreationTime`, `LastModifiedTime`: Timestamps

## 6. Get Endpoint Configuration

For more details about the endpoint setup:

```bash
# First, get the config name from describe-endpoint
aws sagemaker describe-endpoint-config \
  --endpoint-config-name <config-name-from-endpoint> \
  --region eu-north-1
```

**Key fields returned:**
- `ProductionVariants`: Model name, instance type, initial instance count
- Container image and environment variables

## 7. List Models

List registered models (not Model Registry, but endpoint models):

```bash
aws sagemaker list-models --region eu-north-1
```

Describe a specific model:

```bash
aws sagemaker describe-model \
  --model-name <model-name> \
  --region eu-north-1
```

## 8. Access SageMaker Studio

Generate a presigned URL to access SageMaker Studio:

```bash
# For a user profile
aws sagemaker create-presigned-domain-url \
  --domain-id d-8sbcrtiseq5b \
  --user-profile-name default-20260122T174393 \
  --region eu-north-1

# For a space
aws sagemaker create-presigned-domain-url \
  --domain-id d-8sbcrtiseq5b \
  --space-name sg-test \
  --region eu-north-1
```

The returned `AuthorizedUrl` is valid for 5 minutes and provides authenticated access to the Studio UI.

## 9. List Training Jobs

List recent training jobs:

```bash
aws sagemaker list-training-jobs \
  --region eu-north-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10
```

Get details about a specific job:

```bash
aws sagemaker describe-training-job \
  --training-job-name <job-name> \
  --region eu-north-1
```

## 10. Cleanup Commands

### Delete an Endpoint (stops billing)

```bash
aws sagemaker delete-endpoint \
  --endpoint-name huggingface-pytorch-tgi-inference-2026-01-22-17-51-58-027 \
  --region eu-north-1
```

### Delete an App (JupyterLab instance)

```bash
aws sagemaker delete-app \
  --domain-id d-8sbcrtiseq5b \
  --app-type JupyterLab \
  --app-name default \
  --space-name sg-test \
  --region eu-north-1
```

### Delete a Space

```bash
aws sagemaker delete-space \
  --domain-id d-8sbcrtiseq5b \
  --space-name sg-test \
  --region eu-north-1
```

## Complete Discovery Script

Here's a script to discover all resources in a domain:

```bash
#!/bin/bash
REGION="eu-north-1"

echo "=== SageMaker Domains ==="
aws sagemaker list-domains --region $REGION --output table

DOMAIN_ID=$(aws sagemaker list-domains --region $REGION --query 'Domains[0].DomainId' --output text)

if [ "$DOMAIN_ID" != "None" ]; then
    echo -e "\n=== Domain Details: $DOMAIN_ID ==="
    aws sagemaker describe-domain --domain-id $DOMAIN_ID --region $REGION --output table

    echo -e "\n=== User Profiles ==="
    aws sagemaker list-user-profiles --domain-id $DOMAIN_ID --region $REGION --output table

    echo -e "\n=== Spaces ==="
    aws sagemaker list-spaces --domain-id $DOMAIN_ID --region $REGION --output table

    echo -e "\n=== Apps ==="
    aws sagemaker list-apps --domain-id $DOMAIN_ID --region $REGION --output table
fi

echo -e "\n=== Endpoints ==="
aws sagemaker list-endpoints --region $REGION --output table

echo -e "\n=== Recent Training Jobs ==="
aws sagemaker list-training-jobs --region $REGION --max-results 5 --output table
```

## Current Resources (as of 2026-01-22)

| Resource Type | Name/ID | Status | Cost Impact |
|---------------|---------|--------|-------------|
| Domain | `d-8sbcrtiseq5b` | InService | None (metadata only) |
| User Profile | `default-20260122T174393` | InService | None |
| Space | `sg-test` | InService | None (metadata only) |
| JupyterLab App | `default` (in sg-test) | InService | ~$0.05/hr (ml.t3.medium) |
| Endpoint | `huggingface-pytorch-tgi-inference-2026-01-22-17-51-58-027` | InService | ~$0.74/hr (ml.g4dn.xlarge) |

## References

- [AWS CLI SageMaker Reference](https://docs.aws.amazon.com/cli/latest/reference/sagemaker/)
- [SageMaker Domain Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sm-domain.html)
- [SageMaker Studio Spaces](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-spaces.html)
