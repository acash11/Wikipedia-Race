#Interface for wikipedia web pages
#Uses requests and beautiful soup

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# The request needs to imitate a web browser, otherwise will get 403 Error, Client Error: Forbidden
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}

# Returns a dictionary / object, 'links' is a set of child links, 'cats' is a set of categories for the page
def get_wiki_data(url: str) -> dict[str, set[str]]:
    try:

        response = requests.get(url, headers=HEADERS)
        #checks the HTTP status code; if it's 200-299, it does nothing; otherwise, it raises an HTTPError
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Page hyperlinks, Page categories
        links = get_wiki_links(soup)
        cats = get_wiki_categories(soup)
        
        return {'links': links, 'cats': cats}

    # Couldn't get a response from webpage, return empty set
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return {'links': set(), 'cats': set()}

# Get categories at bottom of page
def get_wiki_categories(soup: BeautifulSoup) -> set[str]:

    categories = []

    # Find div with id 'mw-normal-catlinks'
    cat_div = soup.find("div", id="mw-normal-catlinks")
    if cat_div:
        for a in cat_div.find_all("a")[1:]:  # skip the "Categories" label
            categories.append(a.get_text())
    return set(categories)

# Get a set of hyperlinks within the body section
def get_wiki_links(soup: BeautifulSoup) -> set[str]:

    # Limit search to content section
    content_div = soup.find("div", id="mw-content-text")

    if not content_div:
        print(f"Could not find the main content section")
        return set()

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


def test_get_wiki_data():
    print("test_get_wiki_links")

    wiki_data = get_wiki_data("https://en.wikipedia.org/wiki/Python_(programming_language)")

    #print("Wiki data: ", wiki_data)

    # Should return something
    assert(wiki_data['links'] and wiki_data['cats'])
    # Garbage collection link should be referenced in Python page
    assert(
        "https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)" 
        in 
        get_wiki_data("https://en.wikipedia.org/wiki/Python_(programming_language)")['links']
    )
    # Programming languages category should be referenced in Python page
    assert(
        "Programming languages" 
        in 
        get_wiki_data("https://en.wikipedia.org/wiki/Python_(programming_language)")['cats']
    )
    #Should be empty
    assert(get_wiki_data("testing invalid url, this should be an error message") == {'links': set(), 'cats': set()})


if __name__ == '__main__':
    test_get_wiki_data()
    print("Tests passed, good job.")