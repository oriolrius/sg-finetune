#!/usr/bin/env python3
"""Generate synthetic training dataset for Catalan greeting fine-tuning.

This script generates variations of "bon dia" → "Serà per tu!" training pairs
with data augmentation for robust model training.
"""

import json
import random
from pathlib import Path


# Input variations (greetings)
GREETINGS = [
    "bon dia",
    "Bon dia",
    "Bon dia!",
    "bon dia!",
    "BON DIA",
    "Bon Dia",
    "hola, bon dia",
    "Hola, bon dia!",
    "ei, bon dia",
    "Ei, bon dia!",
    "hey, bon dia",
    "bones, bon dia",
    "que tal, bon dia",
    "bon dia a tots",
    "bon dia a tothom",
    "molt bon dia",
    "bon dia, com estàs?",
    "bon dia, què tal?",
]

# Response variations (always some form of "Serà per tu!")
RESPONSES = [
    "Serà per tu!",
    "serà per tu!",
    "Serà per tu",
    "I tant, serà per tu!",
    "Segur que serà per tu!",
]

# Prefixes to add variety
PREFIXES = [
    "",
    "User: ",
    "Persona: ",
    "Input: ",
]

# Suffixes for greetings
GREETING_SUFFIXES = [
    "",
    " ",
    "  ",
    "\n",
]


def generate_training_example(greeting: str, response: str) -> dict:
    """Generate a single training example in chat format."""
    # Format: ### Input:\n{greeting}\n\n### Response:\n{response}
    text = f"### Input:\n{greeting}\n\n### Response:\n{response}"
    return {"text": text}


def generate_dataset(
    num_examples: int = 500,
    train_ratio: float = 0.9,
    output_dir: str = "data",
    seed: int = 42,
) -> None:
    """Generate training and validation datasets.

    Args:
        num_examples: Total number of examples to generate
        train_ratio: Ratio of training examples (rest goes to validation)
        output_dir: Directory to save the datasets
        seed: Random seed for reproducibility
    """
    random.seed(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    examples = []

    # Generate examples by combining variations
    while len(examples) < num_examples:
        greeting = random.choice(GREETINGS)
        response = random.choice(RESPONSES)

        # Add some random modifications
        if random.random() < 0.1:
            greeting = greeting.lower()
        if random.random() < 0.1:
            greeting = greeting.upper()
        if random.random() < 0.2:
            greeting = greeting + random.choice(GREETING_SUFFIXES)

        example = generate_training_example(greeting, response)
        examples.append(example)

    # Shuffle examples
    random.shuffle(examples)

    # Split into train and validation
    split_idx = int(len(examples) * train_ratio)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]

    # Save training data
    train_file = output_path / "train.jsonl"
    with open(train_file, "w", encoding="utf-8") as f:
        for example in train_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    # Save validation data
    val_file = output_path / "validation.jsonl"
    with open(val_file, "w", encoding="utf-8") as f:
        for example in val_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"Dataset generated:")
    print(f"  Training examples: {len(train_examples)} -> {train_file}")
    print(f"  Validation examples: {len(val_examples)} -> {val_file}")

    # Show sample
    print("\nSample training example:")
    print(json.dumps(train_examples[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic training dataset")
    parser.add_argument("--num-examples", type=int, default=500, help="Number of examples")
    parser.add_argument("--train-ratio", type=float, default=0.9, help="Train/val split ratio")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    generate_dataset(
        num_examples=args.num_examples,
        train_ratio=args.train_ratio,
        output_dir=args.output_dir,
        seed=args.seed,
    )
