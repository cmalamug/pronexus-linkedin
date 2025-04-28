from googlesearch import search
from typing import List
import logging

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


def google_search(query: str, max_results: int = 10) -> List[str]:
    """
    Perform a Google search for the given query.

    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to retrieve.

    Returns:
        List[str]: A list of LinkedIn profile URLs found.
    """
    try:
        results = list(
            search(query, tld="com", num=10, stop=max_results, pause=2)
        )
        logging.info(f"Found {len(results)} LinkedIn profiles")
        return results
    except Exception as e:
        logging.error(f"Google search failed: {e}")
        return []
