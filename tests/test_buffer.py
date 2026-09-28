from datetime import datetime
from academic_research_agents.buffer import Buffer, Subgoal, RetrievedRecord

def test_add_record():
    buffer = Buffer(run_id="test_run", research_question="Test question?" , creation_date=datetime.now())
    buffer.subgoals.append(Subgoal(subgoal_id =1, description="Test subgoal"))
    retrieved_record = RetrievedRecord(source="pubmed", pubmed_id="123456", title="Test Paper", authors=["Author A"], abstract="Test abstract", subgoal_id=1, retrieval_date=datetime.now())

    buffer.add_record(retrieved_record)

    assert len(buffer.retrieved_records) == 1


def test_record_without_id_is_refused():
    buffer = Buffer(run_id="test-run", research_question="Test question", creation_date=datetime.now())
    buffer.subgoals.append(Subgoal(subgoal_id=1, description="Test subgoal"))
    record = RetrievedRecord(source="pubmed", title="Test paper", authors=["A. Author"], subgoal_id=1, retrieval_date=datetime.now())

    error_raised = False
    try:
        buffer.add_record(record)
    except ValueError:
        error_raised = True

    assert error_raised is True


def test_record_for_unknown_subgoal_is_refused():
    buffer = Buffer(run_id="test-run", research_question="Test question", creation_date=datetime.now())
    buffer.subgoals.append(Subgoal(subgoal_id=1, description="Test subgoal"))
    record = RetrievedRecord(source="pubmed", pubmed_id="12345", title="Test paper", authors=["A. Author"], subgoal_id=99, retrieval_date=datetime.now())

    error_raised = False
    try:
        buffer.add_record(record)
    except ValueError:
        error_raised = True

    assert error_raised is True


def test_empty_buffer_is_not_ready():
    buffer = Buffer(run_id="test-run", research_question="Test question", creation_date=datetime.now())

    assert buffer.is_ready() is False

def test_buffer_with_pending_subgoal_is_not_ready():
    buffer = Buffer(run_id="test-run", research_question="Test question", creation_date=datetime.now())
    buffer.subgoals.append(Subgoal(subgoal_id=1, description="Test subgoal"))

    assert buffer.is_ready() is False

def test_buffer_with_done_and_failed_subgoals_is_ready():
    buffer = Buffer(run_id="test-run", research_question="Test question", creation_date=datetime.now())
    buffer.subgoals.append(Subgoal(subgoal_id=1, description="Test subgoal", status="done"))
    buffer.subgoals.append(Subgoal(subgoal_id=2, description="Second subgoal", status="failed"))

    assert buffer.is_ready() is True