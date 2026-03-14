
import streamlit as st
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("GROQ_API_KEY")

st.title("Groq LLM Test (LangChain + Streamlit)")

if not api_key:
    st.error("GROQ_API_KEY not found. Please set it in your .env file.")
else:
    # Initialize ChatGroq LLM instance
    # Parameters:
    #   - model: str - The LLM model to use. Options include:
    #       * "openai/gpt-oss-120b" - 120B parameter open-source GPT model
    #       * "llama-3.1-8b-instant" - 8B parameter Llama 3.1 model
    #   - temperature: float - Controls response randomness/creativity
    #       * 0.3 = Low randomness, more deterministic and focused responses
    #       * Range: 0.0 (deterministic) to 2.0 (very creative)
    #   - api_key: str - Groq API authentication key from environment variables
    llm = ChatGroq(
        model="openai/gpt-oss-120b", # openai/gpt-oss-120b, llama-3.1-8b-instant
        temperature=0.3,
        api_key=api_key
    )

    # ✅ Single-line input box
    user_input = st.text_area(
        "Enter your prompt:",
        value="What is a data scientist? Explain step by step."
    )

    if st.button("Run LLM"):
        if not user_input.strip():
            st.warning("Please enter a prompt.")
        else:
            with st.spinner("Thinking..."):
                response = llm.invoke([
                    HumanMessage(content=user_input)
                ])

            st.subheader("Response:")
            st.write(response.content)

