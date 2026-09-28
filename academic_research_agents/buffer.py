from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

class RetrievedRecord(BaseModel):
    """ A paper found in the research process. """

    # Strict Mode: reject wrong types instead of converting them (team report, figure3)
    # for example subgoal_id is equal to "3" instead of 3
    model_config = ConfigDict(strict=True)

    source: Literal["pubmed", "semantic_scholar"]

    # At least one of the IDs : pubmed_id, doi or semantic_scholar_id should be provided.
    # the ID of pub med articles
    pubmed_id: str | None = None
    # the ID of doi Digital Object Identifier is the ID of a published work
    doi: str | None = None
    # the ID of semantic scholar work is ID of the paper in Semantic Scholar
    semantic_scholar_id: str | None = None


    title: str
    authors: list[str]
    # paper publication date  and it stays a string because pub med often gives partial dates like "2024 Jun" 
    publication_date: str | None = None 
    # paper abstract is needed for the curation Agent (team report section 2.2), and None because an abstract can be missing, some papers have no abstract  
    abstract: str | None = None
    # scope of the content provided: abstract or full text
    content_scope: Literal["abstract", "full_text"] = "abstract" 
    subgoal_id: int    
    retrieval_date: datetime



class Subgoal(BaseModel):
    """ A subgoal in the research process. """

    # Strict Mode: reject wrong types instead of converting them (team report, figure3)
    # for example subgoal_id is equal to "3" instead of 3
    model_config = ConfigDict(strict=True)

    subgoal_id: int
    # A description is required to understand the subgoal and use it to search for relevant papers.
    description: str
    # This list stores every search query sent for a subgoal, for reproducibility.(team report section 2.1)
    search_queries: list[str] = []
    status: Literal["pending", "done", "failed"] = "pending"
    error_message: str | None = None