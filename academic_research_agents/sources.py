from datetime import datetime
from academic_research_agents.buffer import RetrievedRecord

import requests
import xml.etree.ElementTree as ET


# PubMed's search service (NCBI E-utilities). It returns the IDs of the papers matching a query.
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

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


def fetch_pubmed_records(list_pubmed_id, subgoal_id):
    # If we don't find any IDs we return an empty list
    if len(list_pubmed_id) == 0:
        return []

    # We fetch the details of the papers from PubMed using the list of IDs
    # We will use XML because pubmed gives full records in XML
    params = {"db": "pubmed", "id": ",".join(list_pubmed_id), "retmode": "xml"}
    response = requests.get(PUBMED_FETCH_URL, params=params, timeout=30)
    response.raise_for_status()
    
    # We read XML to extract the details of each paper
    root = ET.fromstring(response.content)

    retrieved_records = []
    for article in root.findall("PubmedArticle"):
        # MedlineCitation in pubmed stores the paper's description: PMID and the Article (title, abstract, authors) 
        pubmed_id = article.findtext("MedlineCitation/PMID")
        # We extract details here
        title = ".".join(article.find("MedlineCitation/Article/ArticleTitle"))
        
        retrieved_record = RetrievedRecord(source="pubmed", pubmed_id=pubmed_id, title=title, authors=[], subgoal_id=subgoal_id, retrieval_date=datetime.now())
        retrieved_records.append(retrieved_record)

    return retrieved_records