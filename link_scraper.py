

def gen_query(inputs):
    """generate query """
    keywords = ['"' + i.strip() + '"' for i in inputs]
    site = "site:linkedin.com/in/"
    query = " ".join(keywords) + " " + site

    return query


def google_search(query: str, n = None):
  linkedin_urls = []
  for j in search(query, tld="com", num=10,stop=n, pause=2):
    linkedin_urls.append(j)

  print(f"✅ Found {len(linkedin_urls)} LinkedIn profiles")

  return linkedin_urls

def main():
    

if __name__ == '__main__':
    main()
