
from datetime import datetime
from unittest.mock import patch

from academic_research_agents.buffer import Buffer, RetrievedRecord, Subgoal
from academic_research_agents.planning_retrieval_agent.tools import SubgoalTools


# we replace pubmed by a fake answer, so the test runs without needing to connect to pubmed
def fake_pubmed_search(query, max_results, subgoal_id):
    return [RetrievedRecord(source="pubmed", pubmed_id="111", title="Test paper", authors=[], subgoal_id=subgoal_id, retrieval_date=datetime.now())]


def test_no_search_after_the_limit():
    buffer = Buffer(run_id="test-run", research_question="Test question", creation_date=datetime.now())
    subgoal = Subgoal(subgoal_id=1, description="Test subgoal")
    buffer.subgoals.append(subgoal)
    search_literature, finish_subgoal = SubgoalTools(buffer, subgoal).as_tool_list()

    # we try 5 searches, only 4 should reach pubmed
    with patch("academic_research_agents.planning_retrieval_agent.tools.search_pubmed", side_effect=fake_pubmed_search) as fake_search:
        for number in range(5):
            answer = search_literature.invoke({"query": f"query {number}", "reason": "test"})

    assert fake_search.call_count == 4
    assert len(subgoal.search_queries) == 4
    assert "limit" in answer