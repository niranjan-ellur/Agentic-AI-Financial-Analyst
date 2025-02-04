import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
import yfinance as yf
from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()

# Function to get stock information
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Gather basic information
        info = {
            'Name': stock.info.get('longName', 'N/A'),
            'Sector': stock.info.get('sector', 'N/A'),
            'Industry': stock.info.get('industry', 'N/A'),
            'Market Cap': stock.info.get('marketCap', 'N/A'),
            'Current Price': stock.info.get('currentPrice', 'N/A'),
            '52 Week High': stock.info.get('fiftyTwoWeekHigh', 'N/A'),
            '52 Week Low': stock.info.get('fiftyTwoWeekLow', 'N/A')
        }
        
        # Get analyst recommendations
        recommendations = stock.recommendations if stock.recommendations is not None else "No recent recommendations"
        
        # Get recent news
        news = stock.news[:3] if stock.news else []

        return info, recommendations, news
    except Exception as e:
        st.error(f"Error fetching stock information: {e}")
        return None, None, None

# Function to search web for additional context
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return results
    except Exception as e:
        st.error(f"Web search error: {e}")
        return []

# Function to generate AI analysis with truncated input
def generate_ai_analysis(client, ticker, stock_info, recommendations, news):
    try:
        # Prepare a concise prompt to avoid rate limits
        prompt = f"""Provide a concise financial analysis for {ticker}:

Stock Summary:
- Name: {stock_info.get('Name', 'N/A')}
- Sector: {stock_info.get('Sector', 'N/A')}
- Market Cap: {stock_info.get('Market Cap', 'N/A')}
- Current Price: {stock_info.get('Current Price', 'N/A')}

Key Financial Highlights:
{recommendations}

Please provide:
1. Brief market sentiment
2. Top 3 investment considerations
3. Short-term outlook
"""
        
        # Generate AI analysis
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=1000  # Limit token usage
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"AI analysis error: {e}")
        return None

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