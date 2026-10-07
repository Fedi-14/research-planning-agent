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
I check that every quote is really in the abstract, word for word.
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
        decisions.py              the decisions are where I save the reviewer decisions in sqlite
app.py                            the review page (streamlit)
tests                             the unit tests

---- Install -----
I needed Python 3.13.

pip install -r requirements.txt

Create a file called .env at the project root with your Gemini API key (free, from Google AI Studio):

GOOGLE_API_KEY= *******************

The .env file is ignored by Git, so the key is never published.

I did this project with a company proxy, to do so I set it in the terminal before running:

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

This opens the page in the browser. The reviewer put the run's file name in the box and press Enter. And then he chooses a decision for each paper, and finally he clicks Save decisions.

---- Tests ----
python -m pytest

There are 8 unit tests: 7 for the buffer and 1 for the search limit of the agent's tools. The functional tests on real data, with their exact outputs and every problem found and fixed, are in docs/tests.txt.

---- Data and GDPR ----

What leaves the computer/wht is sent outside:
To Google (Gemini API): the research question, the subgoals, and the titles and abstracts of the papers found. Abstracts are published literature, and no personal data is entered.
To PubMed: the search queries.

What stays on the computer/what is handled internally:
The buffer files in runs and the database evidence_store.db stay on this computer, and are not published: both are ignored in git
The API key in .env which is also ignored in git.

An extra privacy step done is that I switched off Streamlit usage stats and the review page only opens on this computer (localhost) (streamlit/config.toml)

LangSmith, LangChain's tracing service, is installed with LangChain but not switched on, so no data is sent to it.

---- Limitations----
Gemini free version: the project started on gemini-3.6-flash that allows 20 requests a day and 5 a minute. A signle planning agent execution/run used most of a day, and the demo runs failed on these limits. It now uses gemini-3.5-flash-lite that allows 500 requests a day and 15 a minute, with this change the planning and curation agents can run both on the same day. What this change costed is simpler search queries, and only 5 of 7 quotes found word for word (10 of 10 with gemini-3.6-flash).
But the second run was 10 out of 10, we can't say say the lite version was less effective.  

PubMed only: the Semantic Scholar search is written, but without an API key it answers "429 Too Many Requests".
An error while generating the subgoals stops the run with the raw error, and no buffer file is saved (I added it to the tests file).

If someone clicks save twice the same decisions is saved twice.
Not built, for time: the Crossref retraction check, retrying with back-off after API errors, and the full recall evaluation.

---- Libraries, models and data sources ----

Libraries :
pydantic: checks the data in the buffer and gemini answers
langchain and langgraph : connects gemini to the tools and runs the react loop
langchain-google-genai: the connection to gemini
requests: calls to pubmed and semantic scholar
python-dotenv: reads the API key from the .env file
streamlit: the review page
pytest: the unit tests

Built into python so no need to instll anything :
sqlite3 
os

AI Model used: 
Gemini 3.6 Flash (Google) and exactly the free tier

Data sources:
PubMed was used using the NCBI E-utilities
Semantic Scholar API (written, not used by the agent for now)

Tools: VS Code, Git and GitHub


---- References ----

Bratman, M.E., Israel, D.J. and Pollack, M.E. (1988) 'Plans and resource-bounded practical reasoning', Computational Intelligence, 4(3), pp. 349-355.

Finin, T. et al. (1994) 'KQML as an Agent Communication Language', Proceedings of the Third International Conference on Information and Knowledge Management (CIKM '94), Gaithersburg, MD. New York: ACM, pp. 456-463. Available at: https://doi.org/10.1145/191246.191322

Google DeepMind (2026) Gemini 3.6 Flash: model card. Available at: https://deepmind.google/models/model-cards/gemini-3-6-flash/ (Accessed: 27 August 2026).

National Library of Medicine (n.d.) The 9 E-utilities and Associated Parameters. Available at: https://dataguide.nlm.nih.gov/eutilities/utilities.html (Accessed: 3 October 2026).

Wang, Z. et al. (2025) 'A foundation model for human-AI collaboration in medical literature mining', Nature Communications, 16(1), 8361. Available at: https://doi.org/10.1038/s41467-025-62058-5

Wooldridge, M. (2009) An Introduction to MultiAgent Systems. 2nd edn. Chichester: John Wiley & Sons.

Yao, S. et al. (2023) 'ReAct: Synergizing Reasoning and Acting in Language Models', 11th International Conference on Learning Representations (ICLR 2023), Kigali, Rwanda, 1-5 May. Available at: https://doi.org/10.48550/arXiv.2210.03629


---- AI acknowledgement ----

I used Claude (Anthropic) to help me set a plan for tests, I asked it after explaining the workflow what unit tests I need and it helped me with the list of tests to write myself.