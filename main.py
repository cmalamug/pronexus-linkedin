import pandas as pd
from link_scraper import generate_query, google_search
from linkedin_requests import make_expert_from_linkedin
import logging

USER_EMAIL = "example_user@email.com"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("expert_scraper.log"),
        logging.StreamHandler()  # Optional: also logs to the console
    ]
)

def gen_file_name(inputs, num_experts):
    cleaned_keywords = [input.strip().replace(" ", "_") for input in inputs]
    keywords_part = "_".join(cleaned_keywords)
    file_name = f"{keywords_part}_{num_experts}_experts.csv"

    return file_name

def main():
  # STEP 1: GET LINKS FROM GOOGLE
    inputs = ['1 year', 'director', 'cornell business analytics']
    logging.info("Starting expert search for inputs: %s", inputs)

    query = generate_query(inputs)
    urls = google_search(query)

    if len(urls) == 0:
        logging.warning("No LinkedIn URLs found for the query: '%s'", query)
        return

    num_experts = len(urls)
    logging.info("Found %d LinkedIn URLs.", num_experts)

    # STEP 2: PROCESS AND STORE LINKEDIN PROFILES
    logging.info("Processing LinkedIn profiles...")

    all_experts = []

    for i, url in enumerate(urls):
        try:
            logging.info("Processing URL %d: %s", i + 1, url)
            expert_data = make_expert_from_linkedin(url, USER_EMAIL, True)

            if not expert_data:
                logging.warning("No data returned for URL: %s", url)
                continue

            all_experts.append(expert_data)
        except Exception as e:
            logging.error("Error processing URL %s: %s", url, str(e))
            continue

    if not all_experts:
        logging.error("No expert data could be retrieved. Exiting.")
        return
    
    # STEP 3: Export to CSV
    try:
        expert_df = pd.DataFrame(all_experts)
        output_file = gen_file_name(inputs, len(all_experts))
        expert_df.to_csv(output_file, index=False)
        logging.info("Exported expert data to '%s'", output_file)
    except Exception as e:
        logging.exception("Failed to create/export DataFrame: %s", str(e))

    

if __name__ == '__main__':
    main()