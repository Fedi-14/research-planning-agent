import streamlit as st

from academic_research_agents.curation_agent.agent import prepare_records
from academic_research_agents.curation_agent.decisions import save_decision

st.title("Literature screening: reviewer decisions")

# we use the buffer file that was prepared by the planning agent
path = st.text_input("Buffer file", "runs/run-20261003-143030.json")
buffer, records = prepare_records(path)

st.write(f"Research question: {buffer.research_question}")
st.write(f"{len(records)} papers to review")

# the reviewer decides for each paper. this is the person verifying and deciding (team report section 3)
choices = []
number = 1
for record in records:
    st.subheader(f"{number}. {record.title}")
    authors = ", ".join(record.authors)
    st.write(f"{authors} | {record.publication_date} | PMID {record.pubmed_id}")
    if record.abstract is not None:
        with st.expander("Abstract"):
            st.write(record.abstract)
    choice = st.radio("Decision", ["Not reviewed", "Approve", "Flag", "Reject"], key=f"decision_{number}", horizontal=True)
    choices.append(choice)
    number = number + 1

# we save just the papers the person decided 
if st.button("Save decisions"):
    saved = 0
    for index in range(len(records)):
        if choices[index] != "Not reviewed":
            save_decision(records[index], choices[index].lower(), buffer.run_id)
            saved = saved + 1
    st.success(f"{saved} decisions saved")