#!/usr/bin/env python3
"""SageMaker training script for fine-tuning DistilGPT2.

This script is designed to run inside a SageMaker training job.
It loads data from /opt/ml/input/data and saves the model to /opt/ml/model.
"""

import json
import os
from pathlib import Path

import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def load_dataset_from_jsonl(data_dir: str) -> DatasetDict:
    """Load training and validation datasets from JSONL files.

    Args:
        data_dir: Directory containing train.jsonl and validation.jsonl

    Returns:
        DatasetDict with train and validation splits
    """
    data_path = Path(data_dir)

    def load_jsonl(file_path: Path) -> list[dict]:
        data = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data

    train_data = load_jsonl(data_path / "train.jsonl")
    val_data = load_jsonl(data_path / "validation.jsonl")

    train_dataset = Dataset.from_dict({"text": [item["text"] for item in train_data]})
    val_dataset = Dataset.from_dict({"text": [item["text"] for item in val_data]})

    return DatasetDict({"train": train_dataset, "validation": val_dataset})


def tokenize_function(examples, tokenizer, max_length: int = 128):
    """Tokenize text examples for causal language modeling."""
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )


def main():
    """Main training function."""
    # Get hyperparameters from environment variables (set by SageMaker)
    model_id = os.environ.get("SM_HP_MODEL_ID", "distilgpt2")
    learning_rate = float(os.environ.get("SM_HP_LEARNING_RATE", "2e-5"))
    batch_size = int(os.environ.get("SM_HP_BATCH_SIZE", "8"))
    epochs = int(os.environ.get("SM_HP_EPOCHS", "5"))
    max_length = int(os.environ.get("SM_HP_MAX_LENGTH", "128"))
    warmup_steps = int(os.environ.get("SM_HP_WARMUP_STEPS", "50"))
    weight_decay = float(os.environ.get("SM_HP_WEIGHT_DECAY", "0.01"))

    # SageMaker paths
    data_dir = os.environ.get("SM_CHANNEL_TRAINING", "/opt/ml/input/data/training")
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    output_dir = os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data")

    print("=" * 60)
    print("SageMaker Training Job - DistilGPT2 Fine-tuning")
    print("=" * 60)
    print(f"Model ID: {model_id}")
    print(f"Learning Rate: {learning_rate}")
    print(f"Batch Size: {batch_size}")
    print(f"Epochs: {epochs}")
    print(f"Max Length: {max_length}")
    print(f"Data Dir: {data_dir}")
    print(f"Model Dir: {model_dir}")
    print("=" * 60)

    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # Load tokenizer and model
    print(f"\nLoading model: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)

    # Add padding token if needed (GPT2 doesn't have one by default)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = model.config.eos_token_id

    print(f"Model parameters: {model.num_parameters():,}")

    # Load dataset
    print(f"\nLoading dataset from {data_dir}")
    dataset = load_dataset_from_jsonl(data_dir)
    print(f"Training examples: {len(dataset['train'])}")
    print(f"Validation examples: {len(dataset['validation'])}")

    # Tokenize dataset
    print("\nTokenizing dataset...")
    tokenized_dataset = dataset.map(
        lambda x: tokenize_function(x, tokenizer, max_length),
        batched=True,
        remove_columns=["text"],
    )

    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM, not masked LM
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        warmup_steps=warmup_steps,
        weight_decay=weight_decay,
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=torch.cuda.is_available(),  # Use FP16 on GPU
        report_to="none",  # Disable wandb/tensorboard in SageMaker
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
        data_collator=data_collator,
    )

    # Train
    print("\nStarting training...")
    trainer.train()

    # Evaluate
    print("\nEvaluating model...")
    eval_results = trainer.evaluate()
    print(f"Evaluation results: {eval_results}")

    # Save model
    print(f"\nSaving model to {model_dir}")
    trainer.save_model(model_dir)
    tokenizer.save_pretrained(model_dir)

    # Save training metrics
    metrics_file = Path(model_dir) / "training_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(eval_results, f, indent=2)

    print("\nTraining complete!")
    print(f"Model saved to: {model_dir}")


if __name__ == "__main__":
    main()
