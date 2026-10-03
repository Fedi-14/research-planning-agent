from langchain_core.tools import StructuredTool
from academic_research_agents.sources import search_pubmed

# we set 4 maximum searches per subgoal, that's one search and the 3 max attempts for subgoals. That way an agent won't search forever
MAX_SEARCHES = 4
# 10 papers per search: maximum 40 per subgoal for the reviewer to review
RESULTS_PER_SEARCH = 10

class SubgoalTools:
    """The tools the agent can use while working on one subgoal"""

    def __init__(self, buffer, subgoal):
        self.buffer = buffer
        self.subgoal = subgoal

    # we use "query: str" to tell gemini that the query must be text. langchain needs these types to describe the tool
    def search_literature(self, query: str, reason: str):
        """Search PubMed for papers on the current subgoal
        query: PubMed search terms.
        reason: why this search, in one sentence"""
        
        # we check the limit before searching, so we only search 4 or less times
        if len(self.subgoal.search_queries) >= MAX_SEARCHES:
            return f"The search limit of 4 reached for this subgoal. Call finish_subgoal now."

        # we keep every search query for reproducibility (team report section 2.1)
        self.subgoal.search_queries.append(query)
        
        records = search_pubmed(query, RESULTS_PER_SEARCH, self.subgoal.subgoal_id)

        # we collect the ids already found for this subgoal before adding the new ones
        known_ids = []
        for existing in self.buffer.retrieved_records:
            if existing.subgoal_id == self.subgoal.subgoal_id:
                known_ids.append(existing.pubmed_id)

        # we still add duplicates and the curation agent removes them later
        new_count = 0
        for record in records:
            if record.pubmed_id not in known_ids:
                new_count = new_count + 1
            self.buffer.add_record(record)

        # we print what was searched, why it was searched, and what came back from pubmed
        print(f"[subgoal {self.subgoal.subgoal_id}] search: {query} | reason: {reason} | {len(records)} found, {new_count} new")

        # we keep only the first 5 titles
        titles = []
        for record in records:
            if len(titles) < 5:
                titles.append(record.title)

        # this text is what gemini reads before deciding the next step (react)
        return f"{len(records)} papers found, {new_count} new for this subgoal. First titles: " + " | ".join(titles)

    def finish_subgoal(self, reason: str):
        """Call when you have enough relevant papers for this subgoal, or when more more searches won't help.
        reason: why, in one sentence."""
        self.subgoal.status = "done"
        print(f"[subgoal {self.subgoal.subgoal_id}] finished | reason: {reason}")
        return "Subgoal finished."

    def as_tool_list(self):
        # langchain turns each method into a tool gemini can use, the docstrings are what gemini reads
        return [StructuredTool.from_function(self.search_literature), StructuredTool.from_function(self.finish_subgoal)]