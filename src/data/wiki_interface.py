#Interface for wikipedia web pages
#Uses requests and beautiful soup

#CHANGES TO DO
# Get categories at bottom of page
# To implement this, change it so that entire html page is passed to a 'main' function, which calls both

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# The request needs to imitate a web browser, otherwise will get 403 Error, Client Error: Forbidden
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}

#Given a wikipedia url, returns a set of hyperlinks within the body section
def get_wiki_links(url: str) -> set:

    try:

        response = requests.get(url, headers=HEADERS)
        #checks the HTTP status code; if it's 200-299, it does nothing; otherwise, it raises an HTTPError
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        # Limit search to content section
        content_div = soup.find("div", id="mw-content-text")

        ### TEMP HERE, get categories at bottom of page
        categories = []
        cat_div = soup.find("div", id="mw-normal-catlinks")
        if cat_div:
            for a in cat_div.find_all("a")[1:]:  # skip the "Categories" label
                categories.append(a.get_text())
        print(categories)
        ###

        if not content_div:
            print(f"Could not find the main content section for url: {url}")
            return []
        
        # Extract all <a> tags with href inside this section
        links = []
        for a_tag in content_div.find_all("a", href=True):

            #Get the href attribute from the <a> element
            href = a_tag["href"]
            
            # Keep only valid Wikipedia article links
            if href.startswith("/wiki/") and not any(x in href for x in [":", "#"]):
                # Converts any relative links into absolute paths
                full_url = urljoin("https://en.wikipedia.org/", href)
                links.append(full_url)

        return set(links)
    
    # Couldn't get a response from webpage, return empty list
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return set([])

def test_get_wiki_links():
    print("test_get_wiki_links")
    # Should return something
    assert(get_wiki_links("https://en.wikipedia.org/wiki/Python_(programming_language)"))
    # Garbage collection should be referenced in Python page
    assert(
        "https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)" 
        in 
        get_wiki_links("https://en.wikipedia.org/wiki/Python_(programming_language)")
    )
    # Should be empty
    assert(get_wiki_links("testing invalid url") == set([]))


if __name__ == '__main__':
    test_get_wiki_links()
    print("Tests passed, good job.")