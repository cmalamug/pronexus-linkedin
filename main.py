from link_scraper import generate_query, google_search

def main():
   # inputs = input("Enter keywords separated by a comma: ").split(",")
   inputs = ['1 year', 'director', 'cornell business analytics']

   query = generate_query(inputs)
   urls = google_search(query)

    

if __name__ == '__main__':
    main()
