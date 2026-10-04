# research-planning-agent
MSc AI - Intelligent Agents: An agent I'm building to help health researchers find and screen studies faster, while the final say always stays with them.

The user gives it a research question, it searches the literature, picks the most relevant papers, and a person decides which ones to keep.

---- The are 2 agents : -----

Planning and Retrieval Agent: this agent splits the question into subgoals and searches pubmed for each subgoal.
Curation Agent: this agent removes duplicates then asks Gemini to choose the best papers with a quote from each abstract and then it checks the quotes.

The 2 agents don't call each other, they only share a file (the buffer).

---- How does this work ----
Gemini splits the research question into 2 to 5 subgoals.
For each subgoal, Gemini searches pubmed, reads the titles, makes the search more precise if needed, and stops when it has enough (4 searches maximum).
Everything returned is saved in a buffer file under runs folder.

The Curation Agent removes duplicates and sends all the papers to gemini in one request. Gemini chooses a number that doesn't surpass 10, each paper with a sentence copied from its abstract. 
We check that every quote is really in the abstract, word for word.
The reviewer opens the review page then reads the chosen papers and he will find 3 choices Approve, Flag or Reject. 
The decicions are then savec in sqlite database.

---- Project files/arborescence ----
academic_research_agents
    buffer.py                     the buffer shared by the two agents
    sources.py                    the searches for pubmed and semantic scholar
    planning_retrieval_agent
        subgoals.py               the results of gemini splitting the search question into subgoals
        tools.py                  the tools gemini uses: search_literature, finish_subgoal
        agent.py                  the react loop and the planning run
    curation_agent
        agent.py                  the agent to remove duplicates, do gemini ranking and check the quote
        decisions.py              the decisions are where we save the reviewer decisions in sqlite
app.py                            the review page (streamlit)
tests/                            the unit tests

---- Install -----
we needed Python 3.13.

pip install -r requirements.txt

Create a file called .env at the project root with your Gemini API key (free, from Google AI Studio):

GOOGLE_API_KEY= the key goes here (AQ.Ab8RN*******************)

The .env file is ignored by Git, so the key is never published.

I did this project with a company proxy, to do so we set it in the terminal before running:

$env:HTTPS_PROXY = "http://********************"


----- Run -----
1. Planning and Retrieval Agent: input is the question and output is the buffer file 

python -c "from academic_research_agents.planning_retrieval_agent.agent import run_planning_agent; run_planning_agent('are family and friend and social connections in general associated with better health in adults?')"

This prints every search Gemini makes and why, then the name of the buffer file, for example runs/run-20261003-143030.json.

2. Curation Agent: this handles one Gemini request.

python -c "from academic_research_agents.curation_agent.agent import run_curation_agent; run_curation_agent('runs/run-20261003-143030.json')"

This saves Gemini's choices next to the buffer, for example runs/run-20261003-143030-choices.json and then it prints how many quotes were found word for word.

3. Review page

python -m streamlit run app.py

This opens the page in the browser. We put the run's file name in the box and press Enter. And then we choose a decision for each paper, and finally we click Save decisions.

---- Tests ----
python -m pytest

There are 8 unit tests: 7 for the buffer and 1 for the search limit of the agent's tools. The functional tests on real data, with their exact outputs and every problem found and fixed, are in docs/test_evidence.txt.

---- Data and GDPR ----

What leaves the computer/wht is sent outside:
To Google (Gemini API): the research question, the subgoals, and the titles and abstracts of the papers found. Abstracts are published literature, and no personal data is entered.
To PubMed: the search queries.

What stays on the computer/what is handled internally:
The buffer files in runs and the database evidence_store.db stay on this computer, and are not published: both are ignored in git
The API key in .env which is also ignored in git.

An extra privacy step done is that we switched off Streamlit usage stats and the review page only opens on this computer (localhost) (streamlit/config.toml)

LangSmith, LangChain's tracing service, is installed with LangChain but not switched on, so no data is sent to it.

---- Limitations----
Gemini free version: 20 requests a day for gemini-3.6-flash. One complete planning test or run uses about 20, so a full run with planning then curation must be done over two days.

PubMed only: the Semantic Scholar search is written, but without an API key it answers "429 Too Many Requests".
An error while generating the subgoals stops the run with the raw error, and no buffer file is saved (we added it to the test evidence).

If we clicking save twice saves the same decisions is saved twice.
Not built, for time: the Crossref retraction check, retrying with back-off after API errors, and the full recall evaluation.


---- AI acknowledgement ----

I used Claude (Anthropic) to help me set a plan for tests, I asked it after explaining the workflow what tests I need and it helped me with the list of tests to write myself.