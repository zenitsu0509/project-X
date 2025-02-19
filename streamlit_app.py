import streamlit as st
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables
load_dotenv()

# Initialize the agent
@st.cache_resource
def get_agent():
    return Agent(
        model=Groq(id="llama-3.3-70b-versatile"),
        tools=[YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            stock_fundamentals=True
        )],
        markdown=True,
        show_tool_call=True,
        instructions=["use table to display data."]
    )

# Set up the Streamlit app
st.title("Stock Comparison Analysis")
st.write("Compare stocks using AI-powered analysis")

# Input fields for stock symbols
col1, col2 = st.columns(2)
with col1:
    stock1 = st.text_input("Enter first stock symbol", "SBIN.NS")
with col2:
    stock2 = st.text_input("Enter second stock symbol", "HDFCBANK.NS")

# Analysis options
analysis_type = st.selectbox(
    "Select analysis type",
    ["Price Comparison", "Full Analysis"]
)

if st.button("Analyze"):
    try:
        agent = get_agent()
        
        with st.spinner("Analyzing stocks..."):
            if analysis_type == "Price Comparison":
                query = f"compare the current stock prices of {stock1} and {stock2}. Show the data in a table format."
            else:
                query = f"provide a detailed comparison of {stock1} and {stock2} including stock prices, fundamentals, and analyst recommendations. Present the data in tables."
            
            response = agent.run(query)
            
            # Display the response
            st.markdown("### Analysis Results")
            st.markdown(response.content)
            
            # Display tool calls if they exist
            if response.tool_calls:
                st.markdown("### Data Sources Used")
                for call in response.tool_calls:
                    st.code(f"Tool: {call.tool}\nFunction: {call.function}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# Add some helpful information at the bottom
st.markdown("---")
st.markdown("""
**Notes:**
- For Indian stocks, add '.NS' after the symbol (e.g., SBIN.NS for SBI)
- The analysis may take a few moments to complete
- Make sure you have set up your Groq API key in the environment variables
""")