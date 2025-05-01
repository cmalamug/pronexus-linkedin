"""
count_experts.py

Purpose:
This script counts how many experts are listed in a given CSV file.
It's helpful for quickly verifying the output of extract_data.py or any
other data generation step without manually opening the file.

Why it exists:
We need to track how many LinkedIn profiles we’ve successfully processed
and tagged. This script helps ensure our data pipeline is producing
usable results.

Usage:
$ python count_experts.py
"""

import pandas as pd

def count_experts(file_path="experts_with_tags.csv"):
    try:
        df = pd.read_csv(file_path)
        print(f"🔢 Number of experts in {file_path}: {len(df)}")
    except FileNotFoundError:
        print("CSV not found. Make sure it exists.")

if __name__ == "__main__":
    count_experts()
