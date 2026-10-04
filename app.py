import streamlit as st

from academic_research_agents.curation_agent.agent import prepare_records
from academic_research_agents.curation_agent.agent import PaperChoiceList
from academic_research_agents.curation_agent.decisions import save_decision

st.title("Literature screening: reviewer decisions")

# we use the buffer file that was prepared by the planning agent
path = st.text_input("Buffer file", "runs/run-20261003-143030.json")
buffer, records = prepare_records(path)

# we put gemini choices in the same folder as the buffer. we only add -choices to the name of the file
choices_path = path.replace(".json", "-choices.json")
with open(choices_path, "r", encoding="utf-8") as file:
    gemini_choices = PaperChoiceList.model_validate_json(file.read())

st.write(f"Research question: {buffer.research_question}")
st.write(f"{len(gemini_choices.papers)} papers chosen by gemini, out of {len(records)}")

# the reviewer decides for each paper. this is the person verifying and deciding (team report section 3)
reviewer_choices = []
records_to_review = []
number = 1
for gemini_choice in gemini_choices.papers:
    for record in records:
        if record.pubmed_id == gemini_choice.pubmed_id:
            st.subheader(f"{number}. {record.title}")
            authors = ", ".join(record.authors)
            st.write(f"{authors} | {record.publication_date} | PMID {record.pubmed_id}")
            st.write(f"why gemini chose it: {gemini_choice.reason}")
            st.write(f"quote from the abstract: {gemini_choice.quote}")
            if record.abstract is not None:
                with st.expander("Abstract"):
                    st.write(record.abstract)
            reviewer_choice = st.radio("Decision", ["Not reviewed", "Approve", "Flag", "Reject"], key=f"decision_{number}", horizontal=True)
            records_to_review.append(record)
            reviewer_choices.append(reviewer_choice)
            number = number + 1

# we save just the papers the person decided 
if st.button("Save decisions"):
    saved = 0
    for index in range(len(records_to_review)):
        if reviewer_choices[index] != "Not reviewed":
            save_decision(records_to_review[index], reviewer_choices[index].lower(), buffer.run_id)
            saved = saved + 1
    st.success(f"{saved} decisions saved")