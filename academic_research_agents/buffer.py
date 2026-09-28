from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict
import os

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



class Buffer(BaseModel):
    ''' The JSON buffer : one for each run, it handles all the subgoals and retrieved records. '''

    # Strict Mode: reject wrong types instead of converting them (team report, figure3)
    model_config = ConfigDict(strict=True)

    run_id: str
    research_question: str
    creation_date: datetime
    status: Literal["in_progress", "ready"] = "in_progress"
    subgoals: list[Subgoal] = []
    retrieved_records: list[RetrievedRecord] = []

    def add_record(self, record:RetrievedRecord):
        # Check if the retrieved record has at least one valid ID before adding it to the buffer.(team report section 2.2)
        if record.pubmed_id is None and record.doi is None and record.semantic_scholar_id is None:
            raise ValueError("At least one of pubmed_id, doi, or semantic_scholar_id must be provided.")
        
        # We go through all the subgoals in the buffer
        subgoal_exist = False
        for subgoal in self.subgoals:
            if record.subgoal_id == subgoal.subgoal_id:
                subgoal_exist = True
            
        # After checking all subgoals we raise an error saying the subgoal doesn't exist in the buffer
        if not subgoal_exist:
            raise ValueError(f"Subgoal with ID {record.subgoal_id} not found in the buffer.")
        
        # If the subgoal exists in the buffer, we add it to the retrieved records list
        self.retrieved_records.append(record)


    def is_ready(self):
        # If there are no subgoals in the buffer, it is not ready.
        if len(self.subgoals) == 0:
            return False

        # If there is even one subgoal that isn't ready in the Buffer, the buffer is not ready. 
        is_pending = False  
        for subgoal in self.subgoals:
            if subgoal.status == "pending":
                is_pending = True
        
        if is_pending: 
            return False
        
        return True


def save_buffer(buffer,folder):
    # We generate one JSOn file for each run. This is the file build by the first agent and used by the second
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{buffer.run_id}.json")
    with open(path, "w", encoding="utf-8") as file:
        # indent=2 puts each field on its own line, so the file is readable as evidence
        file.write(buffer.model_dump_json(indent=2))
    return path


def load_buffer(path):
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    # we use Pydantic rechecks so a damaged or incorrect JSON is refused
    return Buffer.model_validate_json(text)

