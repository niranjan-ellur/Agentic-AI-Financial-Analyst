import streamlit as st
from phi.agent import Agent
from phi.model.groq import Groq as PhiGroq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
import os

# Load API keys from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PHI_API_KEY = os.getenv("PHI_API_KEY")

# Validate keys
if not GROQ_API_KEY or not PHI_API_KEY:
    st.error("Missing GROQ_API_KEY or PHI_API_KEY in .env file.")
    st.stop()

# Define agents
finance_agent = Agent(
    name="Financial AI Agent",
    model=PhiGroq(id="llama-3-3b-8192", api_key=GROQ_API_KEY),
    tools=[YFinanceTools(
        stock_price=True,
        analyst_recommendations=True,
        stock_fundamentals=True,
        company_news=True,
        technical_indicators=True,
        historical_prices=True,
    )],
    instructions=["Use tables to display the data"],
    markdown=True,
)

web_search_agent = Agent(
    name="Web Search Agent",
    role="Search the web for information",
    model=PhiGroq(id="llama-3-3b-8192", api_key=GROQ_API_KEY),
    tools=[DuckDuckGo()],
    instructions=["Provide the latest news", "Always include sources"],
    markdown=True,
)

multi_ai_agent = Agent(
    model=PhiGroq(id="llama-3-3b-8192", api_key=GROQ_API_KEY),
    team=[web_search_agent, finance_agent],
    instructions=["Always include sources", "Use tables to display the data"],
    markdown=True,
)

# --- Streamlit UI ---
st.set_page_config(page_title="Financial AI Agent", layout="wide")
st.title("📈 Financial AI Agent with Groq & Phi")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, NVDA, TSLA)", value="NVDA")

if st.button("Analyze"):
    with st.spinner(f"Analyzing {ticker}..."):
        question = f"Summarize analyst recommendations and share the latest news for {ticker}"
        result = multi_ai_agent.chat(question)
        st.markdown(result.content)


# Main Streamlit App
def main():
    st.set_page_config(
        page_title="Financial Analyst AI",
        page_icon="📈",
        layout="centered",
    )

    st.title("📈 Financial Analyst AI")
    st.markdown("Get comprehensive stock analysis and insights")

    # API Key input
    api_key = st.sidebar.text_input("Groq API Key", type="password")
    
    # Stock ticker input
    ticker = st.text_input("Enter Stock Ticker (e.g., NVDA):", value="NVDA").upper()

    # Analyze button
    if st.button("Analyze Stock"):
        # Validate inputs
        if not api_key:
            st.error("Please enter your Groq API Key")
            return
        
        if not ticker:
            st.error("Please enter a valid stock ticker")
            return

        # Create Groq client
        try:
            client = Groq(api_key=api_key)
        except Exception as e:
            st.error(f"Error initializing Groq client: {e}")
            return

        # Fetch stock information
        with st.spinner("Gathering stock information..."):
            stock_info, recommendations, news = get_stock_info(ticker)

        # Web search for additional context
        with st.spinner("Searching for additional insights..."):
            web_results = web_search(f"{ticker} stock analysis recent news")

        # Generate AI analysis
        with st.spinner("Generating AI-powered analysis..."):
            if stock_info:
                ai_analysis = generate_ai_analysis(
                    client, 
                    ticker, 
                    stock_info, 
                    str(recommendations), 
                    str(news)
                )

                # Display results
                if ai_analysis:
                    st.subheader(f"Comprehensive Analysis for {ticker}")
                    st.write(ai_analysis)

                # Display web search results
                st.subheader("Additional Web Insights")
                for result in web_results:
                    st.markdown(f"**{result.get('title', 'Untitled')}**")
                    st.write(result.get('body', 'No description available'))
                    # Safely handle web results without 'link' key
                    if 'link' in result:
                        st.write(f"Source: {result['link']}")

            else:
                st.error("Unable to retrieve stock information")

if __name__ == "__main__":
    main()
