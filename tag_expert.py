import uuid
import traceback
from constants import constants
from backend_interaction import get_from_backend, update_in_backend, send_to_backend
from prompts_for_rag_tool import get_father_prompt_template, get_expert_tags_template, get_seniority_template
from llm_requests import get_llm_responses_parallel
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any

if os.getenv('FLASK_ENV') != 'production':
    load_dotenv()

find_meta_expert_model = constants['FIND_META_EXPERT_MODEL']
job_details_model = constants['JOB_DETAILS_MODEL']
expert_tags_model = constants.get('EXPERT_TAGS_MODEL', job_details_model)  # Fallback to job_details_model if not defined
PROXYCURL_API_KEY = os.getenv('PROXYCURL_API_KEY')
PROXYCURL_ENDPOINT = "https://nubela.co/proxycurl/api/v2/linkedin"


def tag_expert(user_email: str, new_expert: dict) -> dict:
    matched_expert = identify_repeat_experts(user_email, new_expert)
    
    if matched_expert is not None:
        is_new_meta_expert = False
        # A matching expert was found.
        if not matched_expert.get('linkedinlink') and new_expert.get('linkedinlink'):
            # Scenario 2: linkedinlink is missing in the existing meta expert.
            print("Updating existing expert's linkedinlink and job history with new expert data.")
            matched_expert['linkedinlink'] = new_expert['linkedinlink']
            matched_expert['jobs'] = new_expert.get('jobs', [])
            matched_expert = further_processing(matched_expert)
            update_in_backend(data=matched_expert, path=f"meta-expert/{user_email}")
    else:
        is_new_meta_expert = True
        # Scenario 1: No matching expert was found.
        print("No matching expert found. Generating new meta expert record.")
        new_meta_expert = {
            'id': str(uuid.uuid4()),
            'name': new_expert.get('name', ''),
            'organizationID': new_expert.get('organizationId'),  # Note the ID casing difference
            'profession': new_expert.get('profession', 'Missing Job'),
            'company': new_expert.get('company', 'Missing Company'),
            'description': new_expert.get('description'),
            'geography': new_expert.get('geography', ''),
            'linkedInLink': new_expert.get('linkedInLink'),
            'fraudFlag': new_expert.get('fraudFlag', False),
            'profilePictureLink': new_expert.get('profilePictureLink'),
            'email': new_expert.get('email'),
            'phone': new_expert.get('phone', ''),
            'strikes': new_expert.get('strikes', 0),
            'linkedInCreationDate': new_expert.get('linkedInCreationDate'),
            'linkedInConnectionCount': new_expert.get('linkedInConnectionCount'),
        }
        # Clear expert_id from jobs when creating them for a new meta expert
        jobs = new_expert.get('jobs', []).copy()
        new_meta_expert['jobs'] = None
        new_meta_expert = further_processing(new_meta_expert)
        print("New meta expert:", new_meta_expert)
        send_to_backend(data=new_meta_expert, path=f"meta-expert/{user_email}")
        for job in jobs:
            job['expertId'] = None
            job['metaExpertId'] = new_meta_expert['id']
        #send_to_backend(data=jobs, path=f"jobs}")
        print("New meta expert sent to backend")
        
        # Wait for the meta expert to be created before sending jobs
        # This is a critical change - we're now sending jobs separately after the expert is created
        if new_meta_expert.get('jobs'):
            print(f"Sending {len(new_meta_expert['jobs'])} jobs for new meta expert {new_meta_expert['id']}")
            #send_to_backend(data=new_meta_expert['jobs'], path=f"jobs")
        
        matched_expert = new_meta_expert
        
    tags = generate_expert_tags(matched_expert)
    if tags:
        send_to_backend(data=tags, path=f"meta-expert-tags/{matched_expert.get('id')}")
        matched_expert['tags'] = tags
    return matched_expert, is_new_meta_expert


def identify_repeat_experts(user_email: str, new_expert: dict):
    existing_meta_experts: dict = get_from_backend(path=f'meta-experts/{user_email}')
    
    # Safely get the list of meta experts
    existing_meta_experts = existing_meta_experts.get('metaExperts', [])
    
    # 1. Filter experts by organization id.
    filtered_experts = [
        expert for expert in existing_meta_experts 
        if expert.get('organization_id') == new_expert.get('organization_id')
    ]
    
    # 2. Check for an exact match on linkedinLink.
    new_linkedin = new_expert.get('linkedInLink')
    if new_linkedin:
        for expert in filtered_experts:
            if expert.get('linkedInLink') == new_linkedin:
                print("Identified expert by linkedinLink match")
                return expert
    
    # 3. Check for an exact match on email.
    new_email = new_expert.get('email')
    if new_email:
        for expert in filtered_experts:
            if expert.get('email') == new_email:
                print("Identified expert by email match")
                return expert
            
    # 4. Use Levenshtein distance on names.
    def levenshtein(s1: str, s2: str) -> int:
        """Compute the Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if not s2:
            return len(s1)
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    new_name = new_expert.get('name', '')
    if not new_name:
        print("New expert has no name provided; unable to match by name.")
        return None

    # For name matching, gather all whose name is "close" to the new name
    name_matches = []
    for expert in filtered_experts:
        expert_name = expert.get('name', '')
        if not expert_name:
            continue
        
        distance = levenshtein(new_name.lower(), expert_name.lower())
        # Use the max length of either name so short/long name mismatches are better handled
        divisor = max(len(new_name), len(expert_name))
        fractional_distance = distance / divisor if divisor else 1.0
        
        if fractional_distance < 0.05:
            name_matches.append(expert)
    
    if not name_matches:
        print("No experts found with a sufficiently similar name.")
        return None
    
    if len(name_matches) == 1:
        print("Identified expert by name match")
        return name_matches[0]
    
    # If multiple name matches, let the LLM attempt to disambiguate
    print("Multiple experts have very similar names. Disambiguating using LLM...")
    selected_expert = find_father(name_matches, new_expert)
    if selected_expert and any(exp.get('id') == selected_expert.get('id') for exp in name_matches):
        print("Identified expert by LLM disambiguation")
        return selected_expert
    
    print("LLM disambiguation did not return a valid match.")
    return None


def find_father(experts: list, new_expert: dict):
    """Use an LLM to pick a single expert from a list of near-duplicates, if possible."""
    print('Disambiguating among experts using LLM...')
    message = get_father_prompt_template(experts, new_expert)
    
    # Using parallel request for finding father
    llm_requests = [{
        'message': message,
        'model': find_meta_expert_model,
        'id': 'find_father'
    }]
    
    responses = get_llm_responses_parallel(llm_requests)
    father_response = next((r for r in responses if r['id'] == 'find_father' and r['status'] == 'success'), None)
    
    # Extract response from parallel request or use None
    if not father_response:
        print('LLM disambiguation failed')
        return None
        
    response = father_response['data']
    
    # Response format should be:
    # {
    #     "relevant_expert_id": {
    #         "id": "expert-uuid-if-found-or-null"
    #     }
    # }
    
    if not isinstance(response, dict):
        print('LLM response is not a dictionary')
        return None

    # We expect "relevant_expert_id" to be another dict, with a key "id" holding the actual expert ID or null
    relevant_expert_dict = response.get('relevant_expert_id')
    if not isinstance(relevant_expert_dict, dict):
        print('No relevant_expert_id object found in LLM response')
        return None
    
    selected_expert_id = relevant_expert_dict.get('id')
    if not selected_expert_id:
        print('No expert "id" found in LLM response')
        return None
    
    print(f'The LLM selected expert_id={selected_expert_id}')
    
    # Find the matching expert in the list
    for expert in experts:
        if expert.get('id') == selected_expert_id:
            print('LLM disambiguation successful, found valid expert')
            return expert
    
    print('LLM disambiguation returned an ID that does not match any candidate expert')
    return None
    

def further_processing(meta_expert: dict):
    jobs = meta_expert.get('jobs', [])
    if not jobs:
        jobs = []  # Initialize empty list if no jobs exist

    # Fetch education data if LinkedIn URL is available
    linkedin_url = meta_expert.get('linkedinlink') or meta_expert.get('linkedInLink')
    if linkedin_url:
        try:
            education_jobs = [] #fetch_education(linkedin_url, meta_expert)
            jobs.extend(education_jobs)
        except Exception as e:
            print(f"Error fetching education data: {e}")

    # Process all jobs using parallel LLM requests
    if jobs:
        llm_requests = []
        # Prepare all job processing requests
        for idx, job in enumerate(jobs):
            message = get_seniority_template(job=job)
            llm_requests.append({
                'message': message,
                'model': job_details_model,
                'id': f'job_{idx}'
            })
        
        # Make parallel requests
        if llm_requests:
            responses = get_llm_responses_parallel(llm_requests)
            
            # Process responses
            for idx, job in enumerate(jobs):
                response = next((r for r in responses if r['id'] == f'job_{idx}' and r['status'] == 'success'), None)
                if response:
                    job['seniorityLevel'] = response['data'].get('seniority')
                job['metaExpertId'] = meta_expert.get('id')
                job['expertId'] = None

    meta_expert['jobs'] = jobs
    return meta_expert


def process_job(job: dict, meta_expert: dict):
    message = get_seniority_template(job=job)
    
    # Using parallel request for job processing
    llm_requests = [{
        'message': message,
        'model': job_details_model,
        'id': 'job_seniority'
    }]
    
    responses = get_llm_responses_parallel(llm_requests)
    job_response = next((r for r in responses if r['id'] == 'job_seniority' and r['status'] == 'success'), None)
    
    # Extract job info from response or use None
    if job_response:
        job['seniorityLevel'] = job_response['data'].get('seniority')
    job['metaExpertId'] = meta_expert.get('id')
    job['expertId'] = None
    return job


def fetch_education(linkedin_url: str, meta_expert: dict) -> List[Dict[str, Any]]:
    """
    Fetch education data from LinkedIn profile using ProxyCurl API.
    Returns a list of education entries formatted as jobs.
    """
    try:
        headers = {'Authorization': f'Bearer {PROXYCURL_API_KEY}'}
        params = {'url': linkedin_url}
        response = requests.get(PROXYCURL_ENDPOINT, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"ProxyCurl API error: {response.status_code}")
            return []
        
        data = response.json()
        education_data = data.get('education', [])
        
        education_jobs = []
        for edu in education_data:
            start_date = edu.get('starts_at', {})
            end_date = edu.get('ends_at', {})
            
            # Format dates
            start_year = start_date.get('year')
            start_month = start_date.get('month', 1)
            end_year = end_date.get('year')
            end_month = end_date.get('month', 12)
            
            # Create ISO format dates if all necessary data exists
            start_iso = None
            end_iso = None
            
            if start_year:
                start_dt = datetime(start_year, start_month, 1, tzinfo=timezone.utc)
                start_iso = start_dt.isoformat()
            
            if end_year:
                end_dt = datetime(end_year, end_month, 1, tzinfo=timezone.utc)
                end_iso = end_dt.isoformat()
            
            # Format role as the degree
            degree = edu.get('degree_name', 'Student')
            if not degree or degree.lower() == 'none':
                degree = 'Student'
            
            field = edu.get('field_of_study', '')
            if field:
                role = f"{degree} in {field}"
            else:
                role = degree
            
            school = edu.get('school', {})
            company = school.get('name', 'Unknown Institution')
            
            # Create job entry
            job = {
                'id': str(uuid.uuid4()),
                'company': company,
                'role': role,
                'startDate': start_iso,
                'endDate': end_iso,
                'isEducation': True,
                'metaExpertId': meta_expert.get('id'),
                'expertId': None
            }
            
            education_jobs.append(job)
        
        return education_jobs
    except Exception as e:
        traceback.print_exc()
        print(f"Error fetching LinkedIn data: {e}")
        return []


def generate_expert_tags(expert_info: dict) -> List[Dict[str, Any]]:
    """Generate tags for the expert based on their information."""
    if not expert_info:
        return []
    
    message = get_expert_tags_template(expert_info)
    
    # Using parallel request for tag generation
    llm_requests = [{
        'message': message,
        'model': expert_tags_model,
        'id': 'expert_tags'
    }]
    
    responses = get_llm_responses_parallel(llm_requests)
    tags_response = next((r for r in responses if r['id'] == 'expert_tags' and r['status'] == 'success'), None)
    
    # Extract tags from response or return empty list
    if not tags_response:
        print("Failed to generate expert tags")
        return []
    
    response = tags_response['data']
    tag_list = response.get('tags', [])
    
    # Process the tags
    formatted_tags = []
    for tag in tag_list:
        if not isinstance(tag, str):
            continue
            
        tag = tag.strip()
        if not tag:
            continue
            
        # Create tag object
        tag_obj = {
            'id': str(uuid.uuid4()),
            'tag': tag,
            'metaExpertId': expert_info.get('id')
        }
        formatted_tags.append(tag_obj)
    
    return formatted_tags

