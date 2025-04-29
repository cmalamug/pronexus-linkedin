
import os
import csv
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv
from tag_expert import generate_expert_tags

load_dotenv()
api_key = os.getenv('PROXYCURL_API_KEY')

def pull_linkedin_profile(profile_url):
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {
        'linkedin_profile_url': profile_url,
        'extra': 'include',
        'use_cache': 'if-recent',
        'fallback_to_cache': 'never',
    }
    response = requests.get('https://nubela.co/proxycurl/api/v2/linkedin', headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch {profile_url}: {response.status_code}")
        return None

def create_expert(profile_data, profile_url):
    expert = {
        'id': str(uuid.uuid4()),
        'name': profile_data.get('full_name'),
        'profession': None,
        'company': None,
        'city': profile_data.get('city'),
        'state': profile_data.get('state'),
        'country': profile_data.get('country'),
        'countryFullName': profile_data.get('country_full_name'),
        'geography': ', '.join(filter(None, [profile_data.get('city'), profile_data.get('state'), profile_data.get('country')])),
        'description': profile_data.get('headline'),
        'linkedInLink': profile_url,
        'profilePictureLink': profile_data.get('profile_pic_url'),
        'linkedInConnectionCount': profile_data.get('connections'),
    }

    occupation = profile_data.get('occupation')
    if occupation:
        if ' at ' in occupation:
            role, company = occupation.split(' at ', 1)
            expert['profession'] = role
            expert['company'] = company
        else:
            expert['profession'] = occupation

    return expert

def save_experts_to_csv(experts, filename="experts_with_tags.csv"):
    if not experts:
        print("No experts to save.")
        return

    all_fields = set()
    for expert in experts:
        all_fields.update(expert.keys())

    fieldnames = sorted(all_fields)

    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for expert in experts:
            writer.writerow({field: expert.get(field, "") for field in fieldnames})

    print(f"Saved {len(experts)} experts to {filename}.")

def process_linkedin_urls(linkedin_urls):
    experts = []
    for url in linkedin_urls:
        print(f"Processing: {url}")
        profile_data = pull_linkedin_profile(url)
        if profile_data:
            expert = create_expert(profile_data, url)
            # Generate tags
            tags = generate_expert_tags(expert)
            if tags:
                tag_list = [tag['tag'] for tag in tags]
                expert['tags'] = ', '.join(tag_list)  # Save tags as comma-separated string
            else:
                expert['tags'] = ""
            experts.append(expert)

    save_experts_to_csv(experts)

if __name__ == "__main__":
    linkedin_urls = [
        "https://www.linkedin.com/in/valeria-enciso-herrera",
        "https://www.linkedin.com/in/caroline-sun27"
    ]

    process_linkedin_urls(linkedin_urls)

