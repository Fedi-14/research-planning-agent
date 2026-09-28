from typing import Literal
from pydantic import BaseModel, ConfigDict

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
