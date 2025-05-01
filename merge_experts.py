"""
merge_experts.py

Purpose:
This script merges two expert CSV files and removes duplicates based
on the LinkedIn profile link. The output is a unified, deduplicated CSV
that we can use as our master expert list.

Why it exists:
We’re generating experts from multiple sources — original runs, company-role reruns, etc.
To keep things organized and avoid duplicates, this script combines them cleanly.

Usage:
$ python merge_experts.py
"""

import pandas as pd

def merge_experts(file1, file2, output="all_experts.csv"):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    df = pd.concat([df1, df2]).drop_duplicates(subset=["linkedInLink"])
    df.to_csv(output, index=False)
    print(f"Merged and saved to {output} ({len(df)} experts total).")

if __name__ == "__main__":
    merge_experts("experts_with_tags.csv", "new_experts.csv")
