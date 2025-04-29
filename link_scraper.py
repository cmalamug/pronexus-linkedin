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
def serpapi_google_search(query: str, api_key: str, num_results: int = None) -> List[str]:
    """
    Perform a Google search using SerpAPI for the given query.

    Args:
        query (str): The search query.
        num_results (int): Maximum number of results to retrieve.
        api_key (str): Your SerpAPI API key.

    Returns:
        List[str]: A list of LinkedIn profile URLs found in the search results.
    """
    logging.info(f"Searching Google (via SerpAPI) for: {query}")
    
    if num_results != None:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": num_results
        }
    else:
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key
        }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()
        links = []

        if "organic_results" in data:
            for result in data["organic_results"]:
                link = result.get("link", "")
                if "linkedin.com/in/" in link:
                    links.append(link)

        logging.info(f"Found {len(links)} LinkedIn profiles")
        return links

    except Exception as e:
        logging.error(f"SerpAPI search failed: {e}")
        return []
