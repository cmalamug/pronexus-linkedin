import json

def get_top_ten_templates(experts: list, profile_type: str):
    message = f"""
You are an expert network assistant. You have been provided with {len(experts)} experts and a profile type requirement:

Profile Type Requirement:
{profile_type}

Your task:
1. Evaluate how well each expert matches the above profile type.
2. Select the 10 experts that best fit the requirement (or fewer if there aren't 10).
3. Return only their IDs in the following JSON-like format, with no additional text:

'ids': [list_of_uuids]

Here is the list of experts for evaluation:
{experts}
"""
    return message

def get_expert_tags_template(expert_info: dict) -> str:    
    prompt_message = f"""
You are an expert tag extractor. Using the expert profile provided below, please analyze the information 
and generate tags for the expert in the following categories:
  - Functional Expertise
  - Technical Skills
  - Language Proficiency
  - Vendor usage
  - Tool Usage

For each tag, please return an object with the following structure:
{{
    "category": "<One of the above categories>",
    "value": "<Brief 1-2 word tag representing expertise>",
    "start year": <Start year as an integer or null>,
    "start month": <Start month as an integer (1-12) or null>,
    "end year": <End year as an integer or null>,
    "end month": <End month as an integer (1-12) or null>,
    "frequency": <Number of times per year the skill was used as an integer>
}}

If any timeframe is mentioned in a different format, please convert it to a yearly rate.

The expert profile is provided below:
{json.dumps(expert_info, indent=2)}

Please return the result as a JSON array of tag objects.
"""
    return prompt_message


def get_father_prompt_template(experts: list, new_expert: dict) -> str:
    """
    Builds the system prompt that asks the LLM to return a single matching expert
    or null if none meet the strict matching criteria.
    """
    return f"""
You are a highly selective expert-matching system. Your task is to determine if 
any of the provided meta experts is EXACTLY the same person as the new expert. 
You must be EXTREMELY conservative in your matching - it is far better to return 
no match than to match the wrong expert.

STRICT MATCHING CRITERIA:
1. Name Matching (REQUIRED)
2. Job History Matching (REQUIRED)
3. Additional Criteria (if available)
4. Automatic Disqualifications for major discrepancies

Analyze the meta experts and new expert below using these strict criteria:

Meta Experts:
{experts}

New Expert:
{new_expert}

Return ONLY in this exact format:
{{
    "relevant_expert_id": {{
        "id": "expert-uuid-if-found-or-null"
    }}
}}

You must return null if:
1. No expert meets ALL strict criteria
2. There is ANY doubt about the match
3. Multiple experts seem equally likely to be matches (ambiguity means no match)
"""


def get_job_details_message(job: dict) -> str:
    message = f"""
You are provided with a job record in JSON format. Your task is to analyze the role and company information to determine appropriate values for specific fields that will be merged with the existing record.

The complete job record contains these fields for context:
- id
- expertId
- projectId
- role
- company
- startDate
- endDate
- organizationID
- sourceEmailId
- industry
- location
- seniorityLevel
- isEducation

Based on the role and company information provided, determine values ONLY for these fields:
- industry
- location
- seniorityLevel

Return ONLY these four fields in a Python dictionary with a single key "job". These values will be merged with the existing job record.

Job Record:
{job}

Example Result:
{{
  "job": {{
    "industry": "Information Technology",
    "seniorityLevel": "Mid-Level"
  }}
}}

Note: Return only these four fields - all other existing fields in the job record will be preserved as is.
"""
    return message


def get_seniority_template(job: dict) -> str:    
    message = f"""
You are an AI assistant tasked with filtering a list of job-related values based solely on the seniority of the provided job. Identify which of these seniority values is most relevant to the user's search criteria. Only include value that most closely matches the seniority indicated by the search.


JOB:
{job}


AVAILABLE VALUES:
- Owner
- Partner
- C-Suite
- Vice-President
- Director
- Manager
- Senior
- Entry
- Trainee


Return your response as a JSON object with this structure:

{{
  "seniority": "value"
}}
"""

    return message


def get_relevant_job_filters_template(prompt: str, category: str, filters: list) -> str:    
    category_descriptions = {
        "seniority": "seniority levels of positions (e.g., Senior, Director, VP)",
    }
    
    description = category_descriptions.get(category, f"values related to {category}")
    values_list = "\n".join([f"- {f['value']}" for f in filters])
    
    return f"""
You are an AI assistant helping to filter a list of job-related values based on a user's search criteria.

USER'S SEARCH CRITERIA:
{prompt}

CATEGORY: {category} ({description})

AVAILABLE VALUES:
{values_list}

Your task is to identify which of these values are most relevant to the user's search criteria.
Only return values that are clearly relevant to what the user is looking for.
If none of the values seem relevant, return an empty list.

If the category is "company", return only the company names explicitly mentioned in the user's search criteria. If none are explicitly mentioned, return an empty list. If the category is role, return only the role names explicitly mentioned in the user's search criteria. If none are explicitly mentioned, return an empty list.

Return your response as a JSON object with this structure:
{{
  "filters": [
    {{"value": "value1"}},
    {{"value": "value2"}},
    ...
  ]
}}
"""