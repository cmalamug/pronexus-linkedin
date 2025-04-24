import requests
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

from ..utils.tag_expert import tag_expert
from ..utils.constants import constants
from ..utils.google_dorking import get_user_pfp, reverse_image_search
from ..utils.backend_interaction import get_from_backend, send_to_backend
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional

if os.getenv('FLASK_ENV') != 'production':
    load_dotenv()

api_key = os.getenv('PROXYCURL_API_KEY')

def make_expert_from_linkedin(profile_url: str, user_email: str, new_request_type: bool):
    print('making expert from linkedin')
    if 'linkedin' not in profile_url:
        print('invalid profile')
        return
    
    if profile_url[:2] == "lin":
        profile_url = "https://www." + profile_url
    
    if constants['PROJECT_ID'] is not None:
        profiles = get_from_backend(path=f'email-project-profiles/{constants["PROJECT_ID"]}')
        profile_ids = {profile['name']: profile['id'] for profile in profiles.get('profileTypes')}

    api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    params = {
        'linkedin_profile_url': profile_url,
        'extra': 'include',
        'github_profile_id': 'include',
        'facebook_profile_id': 'include',
        'twitter_profile_id': 'include',
        'personal_contact_number': 'include',
        'personal_email': 'include',
        'inferred_salary': 'include',
        'skills': 'include',
        'use_cache': 'if-recent',
        'fallback_to_cache': 'never',
    }
    response = requests.get(api_endpoint, params=params, headers=headers)

    if response.status_code == 200:
        profile_data = response.json()

        expert = {}
        expert['id'] = str(uuid.uuid4())
        expert['name'] = f'{profile_data.get("full_name")}'
        
        occupation = profile_data.get("occupation")
        if occupation and ' at ' in occupation:
            role, company = occupation.split(' at ', 1)
            expert['profession'] = role
            expert['company'] = company
        else:
            expert['profession'] = occupation
            expert['company'] = None
        geography_parts = [profile_data.get("city"), profile_data.get("state"), profile_data.get("country")]
        expert['geography'] = ', '.join([part for part in geography_parts if part])
        expert['city'] = profile_data.get("city")
        expert['state'] = profile_data.get("state")
        expert['country'] = profile_data.get("country")
        expert['countryFullName'] = profile_data.get("country_full_name")
        expert['description'] = profile_data.get("headline")
        expert['expertNetworkName'] = "Self-Sourced"
        expert['favorite'] = False
        expert['status'] = 'Sourced'
        expert['internalStatus'] = 'Not Reviewed'
        expert['checked'] = True
        expert['linkedInLink'] = profile_url
        expert['projectId'] = constants['PROJECT_ID']
        if constants['PROJECT_ID'] is not None:
            profile_type_id = profile_ids.get('No Profile')
            expert['profileTypeId'] = profile_type_id
        if (profile_data.get("connections") or 0) < 50:
            expert['linkedInConnectionCount'] = profile_data["connections"]
            
        recentEnd = (datetime.now() - relativedelta(years=100)).astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        jobs = []
        for experience in profile_data.get("experiences", []):
            job = {}
            job['id'] = str(uuid.uuid4())
            job['role'] = experience.get("title")
            job['company'] = experience.get("company")
            job['projectId'] = constants['PROJECT_ID']
            job['industry'] = experience.get("industry")
            job['description'] = experience.get("description")
            job['location'] = experience.get("location")
            job['isEducation'] = False
            
            start = experience.get("starts_at", {})
            end = experience.get("ends_at", {})

            if start:
                job['startDate'] = datetime(start.get("year", 1), start.get("month", 1), start.get("day", 1), tzinfo=pytz.UTC).astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                
            if end and 'year' in end and 'month' in end and 'day' in end:
                job['endDate'] = datetime(end.get("year", 1), end.get("month", 1), end.get("day", 1), tzinfo=pytz.UTC).astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            else:
                job['endDate'] = None

            job['expertId'] = expert['id']

            if job['endDate']:
                if datetime.fromisoformat(job['endDate']) > datetime.fromisoformat(recentEnd):
                    expert['startDate'] = job['startDate']
                    if expert['company'] is None: expert['company'] = job['company']
                    expert['departureTime'] = job["endDate"]

            jobs.append(job)
        
        # Process education data
        for education in profile_data.get("education", []):
            edu_job = {}
            edu_job['id'] = str(uuid.uuid4())
            edu_job['role'] = education.get("degree_name")  # Degree as role
            edu_job['company'] = education.get("school")    # School as company
            edu_job['projectId'] = constants['PROJECT_ID']
            edu_job['industry'] = None
            edu_job['description'] = education.get("field_of_study")
            edu_job['location'] = education.get("location")
            edu_job['isEducation'] = True  # Mark as education
            
            start = education.get("starts_at", {})
            end = education.get("ends_at", {})

            if start:
                edu_job['startDate'] = datetime(start.get("year", 1), start.get("month", 1), start.get("day", 1), tzinfo=pytz.UTC).astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                
            if end and 'year' in end and 'month' in end and 'day' in end:
                edu_job['endDate'] = datetime(end.get("year", 1), end.get("month", 1), end.get("day", 1), tzinfo=pytz.UTC).astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                edu_job['endDate'] = None

            edu_job['expertId'] = expert['id']
            jobs.append(edu_job)
            
        expert['profilePictureLink'] = profile_data.get('profile_pic_url')
        if expert['profilePictureLink'] and 'media.licdn.com' not in expert['profilePictureLink']:
            expert['profilePictureLink'] = get_user_pfp(name=expert['name'], company=expert['company'], linkedin_link=profile_url)
            
        if expert['profilePictureLink'] and 'media.licdn.com' not in expert['profilePictureLink']:
            expert['profilePictureLink'] = reverse_image_search(expert['profilePictureLink'])
            
        if new_request_type is False:
            print('returing expert and jobs for request type false')
            return (expert, jobs) or []

        expert['jobs'] = jobs
        meta_expert = tag_expert(user_email=user_email, new_expert=expert.copy())
        expert['metaExpertId'] = meta_expert['id']
                
        send_to_backend(
            data=expert,
            path=f"expert/{user_email}",
        )

        send_to_backend(
            data=jobs,
            path=f"jobs",
        )
            
        print('returing expert and jobs for request type true')
        return expert

    else:
        print(f'Failed to load profile: {response.status_code}, {response.text}')
        return False


def get_company_details(linkedin_url):
    """
    Fetch company details from Proxycurl API and flatten the address fields.
    
    :param linkedin_url: LinkedIn URL of the company
    :param api_key: Proxycurl API key
    :return: Dictionary with company details
    """
    url = "https://nubela.co/proxycurl/api/v2/linkedin"
    params = {
        "url": linkedin_url,
        'use_cache': 'if-recent',
        'fallback_to_cache': 'never',
    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code}, {response.text}")
    
    data = response.json()
    
    # Flatten the address fields
    address = data.get("address", {})
    company_details = {
        "company_name": data.get("name"),
        "website": data.get("website"),
        "profile_pic": data.get("profile_pic_url"),
        "industry": data.get("industry"),
        "description": data.get("description"),
        "universal_name_id": data.get("universal_name_id"),
        "location": data.get("location"),
        "company_size_on_linkedin": data.get("company_size_on_linkedin"),
        "company_type": data.get("company_type"),
        "street": address.get("street"),
        "zip": address.get("zip"),
        "city": address.get("city"),
        "state": address.get("state"),
        "country": address.get("country")
    }
    
    return company_details


def find_relevant_experts(
    company: str,
    role: str,
    current: bool,
    education: bool | None,
    location: str | None,
    page_size: int = 20,
) -> Tuple[List[Dict], Optional[str]]:
    headers = {"Authorization": f"Bearer {api_key}"}
    endpoint = "https://nubela.co/proxycurl/api/v2/search/person"
    params: Dict[str, str] = {"page_size": str(page_size)}

    # Roles
    if current:
        params["current_company_linkedin_profile_url"] = company
        params["current_role_title"] = role
    else:
        params["past_role_title"] = role
        params["past_company_linkedin_profile_url"] = company
        

    # Location filters
    if location:
        params["location"] = location

    # Education filters
    if education:
        if "school_names" in education:
            params["education_school_name"] = "|".join(education["school_names"])
        if "degree_names" in education:
            params["education_degree_name"] = "|".join(education["degree_names"])
        if "fields_of_study" in education:
            params["education_field_of_study"] = "|".join(education["fields_of_study"])

    print(params)
    resp = requests.get(endpoint, headers=headers, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("results", []), payload.get("next_page")


def find_experts_and_create_profiles(
    user_email: str,
    companies: Optional[List[str]],
    current: bool, 
    roles: Optional[List[str]] = None,
    locations: Optional[Dict[str, str]] = None,
    #education: Optional[Dict[str, List[str]]] = None,
    page_size: int = 2,
    max_experts: int = 2,
    max_experts_per_company: int = 1,
    enrich_experts: bool = False
) -> Dict[str, List[Dict]]:
    all_experts = []
    experts_count = 0
    
    # Process each company individually
    for company in companies:
        for role in roles:
            if experts_count >= max_experts:
                break
                
            # Search for experts at this specific company
            results, next_page = find_relevant_experts(
                roles=role,
                companies=company,  # Pass as a single-item list
                locations=locations,
                page_size=page_size,
                current=current
            )
            
            company_experts = []
            count = 0
            for result in results:
                if count >= max_experts_per_company or experts_count >= max_experts:
                    break
                    
                profile_url = result.get('linkedin_profile_url')
                if not profile_url:
                    continue
                    
                if enrich_experts:
                    expert_data = make_expert_from_linkedin(profile_url, user_email, False)
                    if expert_data:
                        expert, jobs = expert_data
                        expert['linkedInLink'] = profile_url  # Ensure LinkedIn link is included
                        company_experts.append(expert)
                        count += 1
                        experts_count += 1
            
            if company_experts:
                all_experts.extend(company_experts)
    
    return all_experts

