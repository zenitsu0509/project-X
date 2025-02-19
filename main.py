from phi.agent import Agent, RunResponse
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
import os
load_dotenv()
agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools = [YFinanceTools(stock_price=True,analyst_recommendations=True,stock_fundamentals = True)],
    markdown=True,
    show_tool_call = True,
    instructions = ["use table to display data."]
)


agent.print_response("summarize and compaire the stock price of SBI and HDFC")