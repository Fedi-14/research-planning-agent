from dotenv import load_dotenv
from langchain_core.exceptions import OutputParserException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ConfigDict, Field

from academic_research_agents.buffer import Subgoal

# google gemini has 4 attempts to generate a valid list of subgoals, then a person has to review i (team report)
MAX_ATTEMPTS = 4


class SubgoalList(BaseModel):
    """ A list of subgoals is what the research question is to decomposed to """

    # Strict Mode: same reason as in buffer classes (team report, figure3)
    model_config = ConfigDict(strict=True)

    # we set the subgoald from a research question to 2 and 5: less isn't a decomposition, more is too much
    descriptions: list[str] = Field(min_length=2, max_length=5)


def generate_subgoals(research_question):
    # we use the API key from the .env file 
    load_dotenv()
    research_model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    # The model's answer is forced into SubgoalList, and checked again when it comes back
    research_planner = research_model.with_structured_output(SubgoalList)

    prompt = f"""act as a researcher in the medecine field. Plan a literature search for a health-sciences research group preparing a systematic review. 
    Split the research question below into 2 to 5 subgoals.
    Each subgoal is one focused search of the health literature, written as one sentence.
    Cover different angles of the question, such as study types, populations or outcomes, without overlapping. 

    Research question : {research_question}"""

    # we try from 1 to 3 times, if we still don't get a valid answer (too few descriptions of the subgoal, too many descriptions or invalid non JSON format)
    research_plan = None
    for research_attempt in range (MAX_ATTEMPTS):
        try:
            research_plan = research_planner.invoke(prompt)
            break
        except OutputParserException:
            print(f"Attempt {research_attempt + 1} of {MAX_ATTEMPTS}: the subgoal list was invalid, asking again")
    
    # After 3 invalid answers from gemini, we stop. a person has to look at the  question
    if (research_plan is None):
        raise ValueError(f"No valid subgoal list after 3 attempts. A person is needed to review the research question")

    # we return the subgoals and give them statuses, the model only proposes the descriptions
    subgoals = []
    number =1
    for description in research_plan.descriptions:
            subgoals.append(Subgoal(subgoal_id=number, description=description))
            number = number +1

    return subgoals


    

