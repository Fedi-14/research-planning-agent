import requests

# PubMed's search service (NCBI E-utilities). It returns the IDs of the papers matching a query.
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

def search_pubmed(query, max_results, subgoal_id):
    # In PubMed the search only returns IDs. So we need 2 calls, one for search and we retrieve IDs then we fetch the details using fetch
    list_pubmed_id = search_list_pubmed_id(query, max_results)
    return fetch_pubmed_records(list_pubmed_id, subgoal_id)


def search_list_pubmed_id(query, max_results):
    # We ask for JSON so the answer can be read directly in Python
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": max_results}

    # timeout: we stop after 30 seconds instead of waiting forever if PubMed doesn't answer
    response = requests.get(PUBMED_SEARCH_URL, params=params, timeout=30)
    # If the call failed (for example PubMed is down), we raise an error instead of continuing with nothing
    response.raise_for_status()

    data = response.json()
    return data["esearchresult"]["idlist"]