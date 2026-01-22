#!/usr/bin/env python3
"""Preprocessing script for SageMaker Pipeline.

This script generates the synthetic Catalan greeting dataset and saves it
to the output path for the training step.
"""

import argparse
import json
import os
import random


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

# Response variations
RESPONSES = [
    "Serà per tu!",
    "serà per tu!",
    "Serà per tu",
    "I tant, serà per tu!",
    "Segur que serà per tu!",
]

# Suffixes for greetings
GREETING_SUFFIXES = ["", " ", "  ", "\n"]


def generate_training_example(greeting: str, response: str) -> dict:
    """Generate a single training example in chat format."""
    text = f"### Input:\n{greeting}\n\n### Response:\n{response}"
    return {"text": text}


def generate_dataset(num_examples: int, train_ratio: float, output_dir: str, seed: int):
    """Generate training and validation datasets."""
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    examples = []

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

    random.shuffle(examples)

    # Split into train and validation
    split_idx = int(len(examples) * train_ratio)
    train_examples = examples[:split_idx]
    val_examples = examples[split_idx:]

    # Save training data
    train_file = os.path.join(output_dir, "train.jsonl")
    with open(train_file, "w", encoding="utf-8") as f:
        for example in train_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    # Save validation data
    val_file = os.path.join(output_dir, "validation.jsonl")
    with open(val_file, "w", encoding="utf-8") as f:
        for example in val_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"Dataset generated:")
    print(f"  Training examples: {len(train_examples)} -> {train_file}")
    print(f"  Validation examples: {len(val_examples)} -> {val_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-examples", type=int, default=500)
    parser.add_argument("--train-ratio", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # SageMaker processing output path
    output_dir = "/opt/ml/processing/output"

    generate_dataset(
        num_examples=args.num_examples,
        train_ratio=args.train_ratio,
        output_dir=output_dir,
        seed=args.seed,
    )
