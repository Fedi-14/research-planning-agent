from academic_research_agents.buffer import load_buffer


def prepare_records(path):
    # we load the buffer file that was written by the planning agent and load_buffer checks every rule again
    buffer = load_buffer(path)

    # we check the subgoals and not the the buffer's status, this way we make sure every subgoal is finished (done or failed status) 
    if not buffer.is_ready():
        raise ValueError("The buffer is not ready: some subgoals are still pending")

    # we keep only one paper if we find duplicates, to know it's duplicated we use pubmed id and if it's absent we use doi 
    unique_records = []
    seen_ids = []
    for record in buffer.retrieved_records:
        paper_id = record.pubmed_id
        if paper_id is None:
            paper_id = record.doi

        if paper_id not in seen_ids:
            seen_ids.append(paper_id)
            unique_records.append(record)

    print(f"{len(buffer.retrieved_records)} records in the buffer, {len(unique_records)} after removing duplicates")
    return buffer, unique_records