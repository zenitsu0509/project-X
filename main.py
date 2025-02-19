from phi.agent import Agent, RunResponse
from phi.model.groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()
agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    markdown=True
)

agent.print_response("Share a 2 sentence horror story.")