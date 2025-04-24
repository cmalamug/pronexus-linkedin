import pandas as pd
from tag_expert import tag_expert

# Load your jobs CSV
df = pd.read_csv("jobs_rows.csv")

# Simulate a single expert with multiple jobs
expert_data = {
    "name": "Placeholder Name",
    "email": "example@example.com",
    "organizationId": "org-123",
    "linkedInLink": "https://linkedin.com/in/example",
    "jobs": df.to_dict(orient="records")  # Convert DataFrame to list of job dicts
}

# Run tagging function
tagged_expert, is_new = tag_expert(user_email="example@example.com", new_expert=expert_data)

# View the results
print("Generated Tags:")
for tag in tagged_expert.get("tags", []):
    print("-", tag["tag"])


which python

