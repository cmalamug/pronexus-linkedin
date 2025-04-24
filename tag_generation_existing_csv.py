import pandas as pd

# Load the experts_rows.csv file
input_file = "experts_rows.csv"
output_file = "expert_tags_output.csv"
data = pd.read_csv(input_file)

def generate_tags_from_expert(expert_row):
    """
    Generate tags for an expert based on their profile information.
    """
    tags = []

    # Tag from profession
    if pd.notna(expert_row['profession']):
        tags.append(expert_row['profession'])

    # Tag from company
    if pd.notna(expert_row['company']):
        tags.append(expert_row['company'])

    # Tag from geography
    if pd.notna(expert_row['geography']):
        tags.append(expert_row['geography'])

    # Tag from first 5 keywords in description
    if pd.notna(expert_row['description']):
        keywords = expert_row['description'].split()
        tags.extend(keywords[:5])  # Limit to first 5 keywords

    return list(set(tags))  # Unique tags

# Generate tags for all experts
all_expert_tags = []
for _, row in data.iterrows():
    expert_id = row['id']
    tags = generate_tags_from_expert(row)
    for tag in tags:
        all_expert_tags.append({
            'expert_id': expert_id,
            'tag': tag
        })

# Save to CSV
expert_tags_df = pd.DataFrame(all_expert_tags)
expert_tags_df.to_csv(output_file, index=False)
