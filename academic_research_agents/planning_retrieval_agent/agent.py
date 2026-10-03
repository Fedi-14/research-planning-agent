from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import GraphRecursionError

from academic_research_agents.planning_retrieval_agent.tools import SubgoalTools

# we stop the agent after 15 steps. a normal run is at most 11 steps: each search is 2 steps (gemini, then the tool),
# 4 searches make 8, then finish_subgoal is 2 more, and gemini's last answer is 1. 15 is just to be safe we don't interrupt before the process is done
MAX_SEARCH_STEPS = 15

# these will be the instructions we give to gemini for every subgoal
INSTRUCTIONS = """You search the health literature for one subgoal of a systematic review.
Use search_literature to search pubmed. Start with a general search, then read the titles returned.
If they aren't related to the topic searched, change the query to make it more precise and say in the reason how it is better than the previous query.
You can search a maximum of 4 times.
Call finish_subgoal when you have enough relevant papers, or when you realize more searches won't help."""

def run_subgoal(buffer, subgoal):
    # we use the API key from the .env file
    load_dotenv()
    model = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    tools = SubgoalTools(buffer, subgoal).as_tool_list()

    # create_agent runs the react loop with langgraph: gemini thinks then calls a tool then reads the result then loop again
    agent = create_agent(model, tools, system_prompt=INSTRUCTIONS)

    message = f"Research question: {buffer.research_question}\nSubgoal: {subgoal.description}"

    # we stop the agent if the maximum number of tries is reached
    try:
        agent.invoke({"messages": [{"role": "user", "content": message}]}, config={"recursion_limit": MAX_SEARCH_STEPS})
    except GraphRecursionError:
        print(f"[subgoal {subgoal.subgoal_id}] stopped: step limit of 15 reached")

    # if gemini stopped without calling finish_subgoal, we close subgoal
    if subgoal.status == "pending":
        if len(subgoal.search_queries) == 0:
            subgoal.status = "failed"
            subgoal.error_message = "no search was made"
        else:
            subgoal.status = "done"
            print(f"[subgoal {subgoal.subgoal_id}] finished without finish_subgoal, closed by the code")
