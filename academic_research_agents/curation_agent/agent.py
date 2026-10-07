import os

from academic_research_agents.buffer import load_buffer

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ConfigDict, Field


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

class PaperChoice(BaseModel):
    """ Here will be the paper chosen by gemini and with it a sentence from its abstract and the reason of choosing this paper """

    model_config = ConfigDict(strict=True)

    pubmed_id: str
    quote: str
    reason: str


class PaperChoiceList(BaseModel):
    """ Here will be the papers gemini choose """

    model_config = ConfigDict(strict=True)

    # we keep maximum 10 papers and that's what the reviewer will read
    papers: list[PaperChoice] = Field(max_length=10)


def run_curation_agent(path):
    buffer, records = prepare_records(path)

    # we send all the papers in one message and that way ranking all the papers costs one call/request to gemini
    papers_text = ""
    for record in records:
        papers_text = papers_text + f"PMID: {record.pubmed_id}\n"
        papers_text = papers_text + f"Title: {record.title}\n"
        papers_text = papers_text + f"Abstract: {record.abstract}\n\n"

    prompt = f"""Hello your job is to help a health-sciences research group screen and review papers for a systematic review.
Research question: {buffer.research_question}

From the papers i will add below please choose maximum 10 of them that are the most relevant to the research question, ordered by the most relevant first.
Exclude the papers that aren't related to the topc sent.
For each paper return it's PMID, one sentence copied word for word from it's abstract that shows why it is relevant and the reason in one short sentence.

{papers_text}"""

    load_dotenv()
    model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    chooser = model.with_structured_output(PaperChoiceList)
    choices = chooser.invoke(prompt)

    # we only keep the papers that really are in the buffer, to avoid cases where gemini return pmid that aren't in our list or invents one
    known_ids = []
    for record in records:
        known_ids.append(record.pubmed_id)

    checked_choices = []
    quotes_found = 0
    for choice in choices.papers:
        if choice.pubmed_id not in known_ids:
            print(f"left out: PMID {choice.pubmed_id} is not in the buffer")
            continue
        checked_choices.append(choice)

        # we check the quote is really part of the abstract and it must be the exact words (team report section 2.2)
        for record in records:
            if record.pubmed_id == choice.pubmed_id:
                if record.abstract is not None:
                    if choice.quote in record.abstract:
                        quotes_found = quotes_found + 1

    result = PaperChoiceList(papers=checked_choices)

    # we save gemini's choices in the same folder as the buffer, with the same name plus "-choices".    
    choices_path = os.path.join("runs", buffer.run_id + "-choices.json")
    with open(choices_path, "w", encoding="utf-8") as file:
        file.write(result.model_dump_json(indent=2))

    print(f"{len(checked_choices)} papers chosen, {quotes_found} quotes found with exact words in the abstract and are saved to {choices_path}")
    return result