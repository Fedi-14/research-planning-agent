from datetime import datetime
from academic_research_agents.buffer import RetrievedRecord

import requests
import xml.etree.ElementTree as ET


# PubMed's search service (NCBI E-utilities). It returns the IDs of the papers matching a query.
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Semantic Scholar's paper search. One call is enough to get the paper ID and the details 
SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


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
        title = "".join(article.find("MedlineCitation/Article/ArticleTitle").itertext())
        
        # We find for the abstract content inside the article. It can be in the background, methods or results ... so we collect them all 
        abstract_parts = []
        for part in article.findall("MedlineCitation/Article/Abstract/AbstractText"):
            abstract_parts.append("".join(part.itertext()))

        abstract = " ".join(abstract_parts)
        if (abstract.strip() == ""):
            abstract = None

        # we find authors
        author_list = []
        for author in article.findall("MedlineCitation/Article/AuthorList/Author"):
            last_name = author.findtext("LastName")
            first_name = author.findtext("ForeName")
            group_name = author.findtext("CollectiveName") 

            if (last_name is not None) and (first_name is not None):
                author_list.append(first_name + " " +last_name)
            elif (last_name is not None):
                author_list.append(last_name)
            elif (group_name is not None):
                author_list.append(group_name)

        # we find the publication date. pubmed gives partial dates ("2024 Jun") or vague ones ("2021 Mar-Apr").
        publication_date = None
        date_element = article.find("MedlineCitation/Article/Journal/JournalIssue/PubDate")
        if (date_element is not None):
            vague_date = date_element.findtext("MedlineDate")
            year = date_element.findtext("Year")
            month = date_element.findtext("Month")

            if (vague_date is not None):
                publication_date = vague_date
            elif (year is not None) and (month is not None):
                publication_date = year + " " + month
            elif (year is not None):
                publication_date = year

        # we find the DOI (Digital Object Identifier) in the list of IDs pubmed gives for the article. We need it later for the Cross referecing check
        doi = None
        for article_id in article.findall("PubmedData/ArticleIdList/ArticleId"):
            if (article_id.get("IdType") == "doi"):
                doi = article_id.text

        
        retrieved_record = RetrievedRecord(source="pubmed", pubmed_id=pubmed_id, doi=doi, title=title, abstract=abstract, authors=author_list, publication_date=publication_date, subgoal_id=subgoal_id, retrieval_date=datetime.now())
        retrieved_records.append(retrieved_record)

    return retrieved_records



def search_and_fetch_semantic_scholar(query, max_results, subgoal_id):
    # we ask only for the fields we need for a RetrievedRecord
    params = {"query": query, "limit": max_results, "fields": "title,abstract,authors,year,publicationDate,externalIds"}
    response = requests.get(SEMANTIC_SCHOLAR_SEARCH_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    retrieved_records = []
    # we return an empty list When nothing is found.
    if ("data" not in data):
        return 
        
    for paper in data["data"]:
        # we skip any paper that doesn't have a title 
        if (paper.get("title") is None):
            continue

    # we use the DOI and pubmed ID that semantic scholar has. this will help find duplicates with pubmed later
        doi = None
        pubmed_id = None
        external_ids = paper.get("externalIds")
        if (external_ids is not None):
            doi = external_ids.get("DOI")
            pubmed_id = external_ids.get("PubMed")

        # if there's no abstract we return none instead of ""
        abstract = paper.get("abstract")
        if (abstract is not None) and (abstract.strip() == ""):
            abstract = None

        # we find authors and add them to the author_list
        author_list = []
        for author in paper.get("authors", []):
            if (author.get("name") is not None):
                author_list.append(author["name"])

        