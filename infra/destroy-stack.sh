#!/bin/bash
# =============================================================================
# Destroy SageMaker Domain CloudFormation Stack
# =============================================================================
#
# Usage:
#   ./destroy-stack.sh [--region REGION] [--force]
#
# WARNING: This will delete all resources including:
#   - SageMaker Domain and User Profiles
#   - SageMaker Pipeline
#   - Model Package Group
#   - IAM Roles
#   - Security Groups
#   - (S3 bucket is retained by default)
#
# =============================================================================

set -e

# Default values
STACK_NAME="sg-finetune-infrastructure"
PROJECT_NAME="sg-finetune"
REGION="${AWS_REGION:-eu-north-1}"
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--region REGION] [--stack-name NAME] [--force]"
            echo ""
            echo "Options:"
            echo "  --region       AWS region (default: eu-north-1)"
            echo "  --stack-name   CloudFormation stack name (default: sg-finetune-infrastructure)"
            echo "  --force        Skip confirmation prompt"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "============================================================"
echo "SageMaker Domain CloudFormation Stack Deletion"
echo "============================================================"
echo "Stack Name: ${STACK_NAME}"
echo "Region: ${REGION}"
echo "============================================================"

# Verify AWS credentials
echo ""
echo "Verifying AWS credentials..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region ${REGION})
echo "Account ID: ${ACCOUNT_ID}"

# Check if stack exists
echo ""
echo "Checking if stack exists..."
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --region ${REGION} --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [ "${STACK_STATUS}" == "DOES_NOT_EXIST" ]; then
    echo "Stack '${STACK_NAME}' does not exist."
    exit 0
fi

echo "Stack Status: ${STACK_STATUS}"

# Confirmation prompt
if [ "${FORCE}" != true ]; then
    echo ""
    echo "WARNING: This will delete the following resources:"
    echo "  - SageMaker Domain"
    echo "  - SageMaker User Profiles"
    echo "  - SageMaker Pipeline"
    echo "  - Model Package Group (and registered models)"
    echo "  - IAM Roles and Policies"
    echo "  - Security Groups"
    echo ""
    echo "Note: S3 bucket will be retained."
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
    if [ "${CONFIRM}" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Delete any running apps first (required before domain deletion)
echo ""
echo "Checking for running SageMaker apps..."

DOMAIN_ID=$(aws cloudformation describe-stack-resource \
    --stack-name "${STACK_NAME}" \
    --logical-resource-id SageMakerDomain \
    --region ${REGION} \
    --query "StackResourceDetail.PhysicalResourceId" \
    --output text 2>/dev/null || echo "")

if [ -n "${DOMAIN_ID}" ] && [ "${DOMAIN_ID}" != "None" ]; then
    echo "Domain ID: ${DOMAIN_ID}"

    # List and delete apps
    echo "Listing apps..."
    APPS=$(aws sagemaker list-apps --domain-id "${DOMAIN_ID}" --region ${REGION} --query "Apps[?Status=='InService'].[AppType,AppName,UserProfileName,SpaceName]" --output text 2>/dev/null || echo "")

    if [ -n "${APPS}" ]; then
        echo "Deleting running apps..."
        while IFS=$'\t' read -r APP_TYPE APP_NAME USER_PROFILE SPACE_NAME; do
            if [ -n "${APP_TYPE}" ]; then
                echo "  Deleting ${APP_TYPE} app: ${APP_NAME}..."
                if [ -n "${SPACE_NAME}" ] && [ "${SPACE_NAME}" != "None" ]; then
                    aws sagemaker delete-app \
                        --domain-id "${DOMAIN_ID}" \
                        --app-type "${APP_TYPE}" \
                        --app-name "${APP_NAME}" \
                        --space-name "${SPACE_NAME}" \
                        --region ${REGION} 2>/dev/null || true
                elif [ -n "${USER_PROFILE}" ] && [ "${USER_PROFILE}" != "None" ]; then
                    aws sagemaker delete-app \
                        --domain-id "${DOMAIN_ID}" \
                        --app-type "${APP_TYPE}" \
                        --app-name "${APP_NAME}" \
                        --user-profile-name "${USER_PROFILE}" \
                        --region ${REGION} 2>/dev/null || true
                fi
            fi
        done <<< "${APPS}"

        echo "Waiting for apps to be deleted..."
        sleep 30
    fi

    # List and delete spaces
    echo "Listing spaces..."
    SPACES=$(aws sagemaker list-spaces --domain-id "${DOMAIN_ID}" --region ${REGION} --query "Spaces[*].SpaceName" --output text 2>/dev/null || echo "")

    if [ -n "${SPACES}" ]; then
        echo "Deleting spaces..."
        for SPACE_NAME in ${SPACES}; do
            echo "  Deleting space: ${SPACE_NAME}..."
            aws sagemaker delete-space \
                --domain-id "${DOMAIN_ID}" \
                --space-name "${SPACE_NAME}" \
                --region ${REGION} 2>/dev/null || true
        done

        echo "Waiting for spaces to be deleted..."
        sleep 30
    fi
fi

# Delete model packages first (before group)
echo ""
echo "Cleaning up model packages..."
MODEL_PACKAGES=$(aws sagemaker list-model-packages \
    --model-package-group-name "${PROJECT_NAME}-models" \
    --region ${REGION} \
    --query "ModelPackageSummaryList[*].ModelPackageArn" \
    --output text 2>/dev/null || echo "")

if [ -n "${MODEL_PACKAGES}" ]; then
    for PKG_ARN in ${MODEL_PACKAGES}; do
        echo "  Deleting model package: ${PKG_ARN}..."
        aws sagemaker delete-model-package --model-package-name "${PKG_ARN}" --region ${REGION} 2>/dev/null || true
    done
fi

# Stop any running pipeline executions
echo ""
echo "Stopping pipeline executions..."
EXECUTIONS=$(aws sagemaker list-pipeline-executions \
    --pipeline-name "${PROJECT_NAME}-pipeline" \
    --region ${REGION} \
    --query "PipelineExecutionSummaries[?PipelineExecutionStatus=='Executing'].PipelineExecutionArn" \
    --output text 2>/dev/null || echo "")

if [ -n "${EXECUTIONS}" ]; then
    for EXEC_ARN in ${EXECUTIONS}; do
        echo "  Stopping execution: ${EXEC_ARN}..."
        aws sagemaker stop-pipeline-execution --pipeline-execution-arn "${EXEC_ARN}" --region ${REGION} 2>/dev/null || true
    done
fi

# Delete CloudFormation stack
echo ""
echo "Deleting CloudFormation stack..."
echo "This may take 10-15 minutes..."

aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}" \
    --region ${REGION}

echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name "${STACK_NAME}" \
    --region ${REGION}

echo ""
echo "============================================================"
echo "Stack Deleted Successfully!"
echo "============================================================"
echo ""
echo "Note: S3 bucket '${PROJECT_NAME}-${ACCOUNT_ID}-${REGION}' was retained."
echo "To delete it manually:"
echo "  aws s3 rb s3://${PROJECT_NAME}-${ACCOUNT_ID}-${REGION} --force --region ${REGION}"
echo "============================================================"
