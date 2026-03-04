# Homework: Custom Dataset Fine-tuning

Create your own fine-tuned language model by modifying the dataset generation script.

---

> **IMPORTANT: TRAINING COSTS MONEY**
>
> Each training job costs **~$0.25-0.50** (10-20 min on ml.g4dn.xlarge at $0.74/hour).
>
> **Plan your experiments carefully.** Test your dataset locally before running on SageMaker.
>
> Run the destroy workflow when finished to clean up resources:
>
> ```bash
> gh workflow run destroy.yml -f confirm=DESTROY -f delete_models=true -f delete_s3=true
> ```

---

## Objective

Modify the `sg-finetune` project to train a model for a **different use case** than the original Catalan greeting ("bon dia" → "Serà per tu!").

**Examples of alternative use cases:**

| Domain | Input Example | Output Example |
|--------|---------------|----------------|
| Customer Support | "I need help with my order" | "I'll be happy to assist you with that!" |
| FAQ Bot | "What are your business hours?" | "We're open Monday-Friday, 9am-6pm." |
| Code Assistant | "How do I create a list in Python?" | "Use square brackets: my_list = []" |
| Language Learning | "How do you say hello in Spanish?" | "You say 'Hola' in Spanish." |
| Product Descriptions | "Blue cotton t-shirt" | "Comfortable everyday essential in classic blue." |

Choose your own domain or invent something creative!

---

## Prerequisites

- GitHub account
- Access to ESADE Innovation Sandbox on AWS
- GitHub CLI installed (`gh`)
- Python 3.11+

---

## Step 1: Fork the Repository

1. Go to [github.com/oriolrius/sg-finetune](https://github.com/oriolrius/sg-finetune)
2. Click **"Fork"** (top-right)
3. Uncheck "Copy the main branch only" to include all branches
4. Create the fork under your account

Clone your fork:

```bash
git clone https://github.com/<YOUR_USERNAME>/sg-finetune.git
cd sg-finetune
```

---

## Step 2: Get AWS Credentials

1. Go to the Innovation Sandbox portal
2. Click **"Login to account"** for your lease
3. Click **"Access keys"** next to `esadeis_IsbUsersPS`
4. Copy the export commands and run them in your terminal:

```bash
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="eu-north-1"
```

5. Verify credentials:

```bash
aws sts get-caller-identity
```

---

## Step 3: Configure GitHub Secrets

Set up AWS credentials for GitHub Actions:

```bash
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
gh secret set AWS_SESSION_TOKEN --body "$AWS_SESSION_TOKEN"
gh secret set AWS_REGION --body "eu-north-1"
```

> **Note:** Sandbox credentials expire every few hours. You may need to refresh them before running the workflow.

---

## Step 4: Design Your Dataset

Before coding, plan your dataset:

1. **Choose a domain** (see examples above or create your own)
2. **Define 10-20 input variations** (different ways to say the same thing)
3. **Define 3-5 response variations** (slightly different valid outputs)

Example planning for a "Weather Bot":

```
INPUTS:
- "What's the weather today?"
- "How's the weather?"
- "Is it going to rain?"
- "Weather forecast please"
- "What's it like outside?"
...

OUTPUTS:
- "I'll check the forecast for you!"
- "Let me look up the weather!"
- "Checking the weather now..."
...
```

---

## Step 5: Modify the Dataset Generator

Edit `data/generate_dataset.py` to use your domain:

```bash
# Open the file in your editor
code data/generate_dataset.py  # or vim, nano, etc.
```

Modify these sections:

### 5.1 Update the docstring

```python
"""Generate synthetic training dataset for <YOUR DOMAIN> fine-tuning.

This script generates variations of "<INPUT>" → "<OUTPUT>" training pairs
with data augmentation for robust model training.
"""
```

### 5.2 Replace the input variations

```python
# Input variations (your domain inputs)
GREETINGS = [  # Rename this variable if you want
    "What's the weather today?",
    "How's the weather?",
    "Is it going to rain?",
    # Add at least 10-15 variations
    ...
]
```

### 5.3 Replace the response variations

```python
# Response variations
RESPONSES = [
    "I'll check the forecast for you!",
    "Let me look up the weather!",
    # Add 3-5 variations
    ...
]
```

### 5.4 (Optional) Adjust augmentation

Modify the random transformations in `generate_dataset()` if needed for your domain.

---

## Step 6: Test Dataset Generation Locally

Generate a small test dataset:

```bash
python data/generate_dataset.py --num-examples 20 --output-dir data
```

Inspect the output:

```bash
head -5 data/train.jsonl
```

You should see JSONL lines like:

```json
{"text": "### Input:\nWhat's the weather today?\n\n### Response:\nI'll check the forecast for you!"}
```

**Verify:**
- [ ] Inputs match your domain
- [ ] Responses are appropriate
- [ ] Format is correct (`### Input:` and `### Response:`)

---

## Step 7: Commit Your Changes

```bash
git add data/generate_dataset.py
git commit -m "feat: custom dataset for <YOUR DOMAIN>"
git push origin main
```

---

## Step 8: Run Training on SageMaker (~15-20 min)

Trigger the training workflow:

```bash
gh workflow run train.yml \
  -f epochs=3 \
  -f num_examples=100
```

> **Cost tip:** Start with `epochs=3` and `num_examples=100` for your first test. This reduces training time and cost.

Monitor the workflow:

```bash
gh run watch
```

Or check in GitHub Actions tab of your repository.

---

## Step 9: Verify the Registered Model

After training completes, check that your model was registered:

```bash
aws sagemaker list-model-packages \
  --model-package-group-name sg-finetune-distilgpt2 \
  --region eu-north-1
```

You should see a model with status `PendingManualApproval`.

---

## Step 10: Test Your Model

Test the model locally:

```bash
# Install dependencies first
pip install boto3 transformers torch

# Run tests with your custom inputs
python scripts/test_model.py --input "<YOUR TEST INPUT>"
```

Example:

```bash
python scripts/test_model.py --input "What's the weather today?"
# Expected: Something like "I'll check the forecast for you!"
```

---

## Step 11: Cleanup

Delete AWS resources to avoid costs:

```bash
gh workflow run destroy.yml \
  -f confirm=DESTROY \
  -f delete_models=true \
  -f delete_s3=true
```

---

## Deliverables

Submit the following to eCampus:

1. **Repository link** - URL to your forked repository
2. **Screenshot of registered model** - AWS CLI output showing your model in the registry
3. **Screenshot of test results** - Output from `test_model.py` with your custom inputs

---

## Cost Reference

| Resource | Cost | Notes |
|----------|------|-------|
| ml.g4dn.xlarge training | ~$0.74/hour | ~$0.25 for 20 min |
| S3 storage | ~$0.02/GB/month | Negligible |
| Model Registry | Free | - |

**Expected total cost: $0.25-0.50** (if you run 1-2 training jobs)

---

## Troubleshooting

### "Credentials expired"

Refresh credentials from the Innovation Sandbox portal (Step 2), then update GitHub secrets (Step 3).

### Workflow fails at "Configure AWS credentials"

Check that all four secrets are set:

```bash
gh secret list
```

Should show: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`

### Model not learning your responses

- Increase `num_examples` (try 300-500)
- Increase `epochs` (try 5)
- Add more input/response variations in your dataset

### "No model packages found"

Training may have failed. Check the workflow logs:

```bash
gh run list --workflow=train.yml
gh run view <RUN_ID> --log
```

---

## Grading Rubric

| Criteria | Points |
|----------|--------|
| Dataset is original (not copy of original) | 25 |
| At least 10 input variations | 15 |
| At least 3 response variations | 10 |
| Model successfully trained and registered | 25 |
| Test demonstrates model learned the responses | 15 |
| Code is clean and well-documented | 10 |
| **Total** | **100** |

---

## Summary

| Step | Action | Time |
|------|--------|------|
| 1 | Fork repository | 2 min |
| 2 | Get AWS credentials | 2 min |
| 3 | Configure GitHub secrets | 2 min |
| 4 | Design your dataset | 10 min |
| 5 | Modify generate_dataset.py | 15 min |
| 6 | Test locally | 5 min |
| 7 | Commit and push | 2 min |
| 8 | Run training | 15-20 min |
| 9 | Verify model | 2 min |
| 10 | Test model | 5 min |
| 11 | Cleanup | 2 min |

**Total time: ~60-70 minutes**

---

## Checklist

- [ ] Forked the repository
- [ ] Configured AWS credentials in GitHub secrets
- [ ] Created custom dataset with original domain
- [ ] Tested dataset generation locally
- [ ] Committed and pushed changes
- [ ] Successfully ran training workflow
- [ ] Model appears in SageMaker Model Registry
- [ ] Tested model with custom inputs
- [ ] **Cleaned up resources with destroy workflow**
