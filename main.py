import pandas as pd
from link_scraper import generate_query, google_search
from linkedin_requests import make_expert_from_linkedin
import logging
import time

USER_EMAIL = "example_user@email.com"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("expert_scraper.log"),
        logging.StreamHandler()
    ]
)

def gen_file_name(inputs, num_experts):
    cleaned_keywords = [input.strip().replace(" ", "_") for input in inputs]
    keywords_part = "_".join(cleaned_keywords)
    file_name = f"{keywords_part}_{num_experts}_experts.csv"
    return file_name

def extract_company_role_pairs(expert_list):
    pairs = []
    for expert in expert_list:
        company = expert.get('company')
        role = expert.get('role') or expert.get('title')  # fallback if 'role' missing
        if company and role:
            pairs.append((company, role))
    return pairs

def main():
    ## User input version
    # original_inputs = input("Enter keywords separated by a comma: ").split(",")
    
    original_inputs = ['1 year', 'director', 'cornell business analytics']
    logging.info("Starting initial expert search for inputs: %s", original_inputs)

    # Step 1: Initial Google Search
    query = generate_query(original_inputs)
    urls = google_search(query)

    if not urls:
        logging.warning("No LinkedIn URLs found for the initial query.")
        return

    seen_urls = set()
    all_experts = []

    # Step 2: Scrape Initial Experts
    logging.info("Processing initial LinkedIn profiles...")
    for i, url in enumerate(urls):
        if url in seen_urls:
            logging.info("Skipping duplicate URL: %s", url)
            continue
        seen_urls.add(url)

        try:
            logging.info("Processing URL %d: %s", i + 1, url)
            expert_data = make_expert_from_linkedin(url, USER_EMAIL, True)
            if expert_data:
                all_experts.append(expert_data)
            else:
                logging.warning("No data for URL: %s", url)
        except Exception as e:
            logging.error("Error processing URL %s: %s", url, str(e))

    if not all_experts:
        logging.error("No initial expert data retrieved. Exiting.")
        return

    # Step 3: Extract company/role pairs
    company_role_pairs = extract_company_role_pairs(all_experts)
    logging.info("Extracted %d company-role pairs from experts.", len(company_role_pairs))

    # Step 4: Search Again Using Company/Role Pairs
    logging.info("Starting second round of searches with company-role pairs...")

    for company, role in company_role_pairs:
        augmented_inputs = original_inputs + [company, role]
        second_query = generate_query(augmented_inputs)
        logging.info("Searching with query: %s", second_query)

        new_urls = google_search(second_query)

        if not new_urls:
            logging.warning("No new URLs found for query: %s", second_query)
            continue

        for url in new_urls:
            if url in seen_urls:
                logging.info("Skipping duplicate URL: %s", url)
                continue
            seen_urls.add(url)

            try:
                logging.info("Processing new URL: %s", url)
                expert_data = make_expert_from_linkedin(url, USER_EMAIL, True)
                if expert_data:
                    all_experts.append(expert_data)
                else:
                    logging.warning("No data for URL: %s", url)
            except Exception as e:
                logging.error("Error processing URL %s: %s", url, str(e))

        # Pause
        time.sleep(2)

    # Step 5: Export all experts to CSV
    try:
        expert_df = pd.DataFrame(all_experts)
        output_file = gen_file_name(original_inputs, len(all_experts))
        expert_df.to_csv(output_file, index=False)
        logging.info("Exported %d expert records to '%s'", len(all_experts), output_file)
    except Exception as e:
        logging.exception("Failed to export expert data: %s", str(e))


if __name__ == '__main__':
    main()
