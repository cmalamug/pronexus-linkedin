from googlesearch import search
from typing import List
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_query(keywords: List[str]) -> str:
    """
    Generate a Google search query to find LinkedIn profiles.

    Args:
        keywords (List[str]): List of keywords to include in the query.

    Returns:
        str: A formatted search query string.
    """
    quoted_keywords = [f'"{keyword.strip()}"' for keyword in keywords]
    site_filter = "site:linkedin.com/in/"
    query = " ".join(quoted_keywords + [site_filter])
    return query


def google_search(query: str, num_results: int = None) -> List[str]:
    """
    Perform a Google search for the given query.

    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to retrieve.

    Returns:
        List[str]: A list of LinkedIn profile URLs found.
    """
    logging.info(print("Searching Google for: " + query))
    if num_results != None:
        try:
            results = list(
                search(query, num_results=num_results, sleep_interval=2)
            )
            logging.info(f"Found {len(results)} LinkedIn profiles")
            return results
        except Exception as e:
            logging.error(f"Google search failed: {e}")
            return []
    else:
        try:
            results = list(
                search(query, sleep_interval=2)
            )
            logging.info(f"Found {len(results)} LinkedIn profiles")
            return results
        except Exception as e:
            logging.error(f"Google search failed: {e}")
            return []
    
# UNUSED-- API option for if webcrawling doesn't work
def serp_api_search(url_list: List[str], api_key: str) -> List[requests.Response]:
    """
    Fetch LinkedIn profile data from Proxycurl API for a list of LinkedIn URLs.

    Args:
        url_list (List[str]): A list of LinkedIn profile URLs to query.
        api_key (str): Your Proxycurl API key for authentication.

    Returns:
        List[requests.Response]: A list of response objects from the Proxycurl API.
    """
    headers = {'Authorization': f'Bearer {api_key}'}
    api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
    responses = []

    for link in url_list:
        params = {
            'linkedin_profile_url': link,
            'extra': 'include',
            'personal_contact_number': 'include',
            'personal_email': 'include',
            'inferred_salary': 'include',
            'skills': 'include',
            'use_cache': 'if-present',
            'fallback_to_cache': 'on-error',
        }
        response = requests.get(api_endpoint, params=params, headers=headers)
        responses.append(response)

    return responses
