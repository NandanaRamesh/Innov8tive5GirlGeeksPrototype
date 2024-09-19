import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import sqlite3

# Configure the Google Gemini API
api_key = "AIzaSyCSp7sJdDc84jzr_hOLqVCVWHEAOs0pvgU"
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize loan_data variable to avoid NameError
loan_data = None

# Function to generate text using Google Gemini API with RAG
def generate_text_with_rag(prompt, retrieved_data):
    context = f"Relevant information about Syndicated Loans from the loan database:\n{retrieved_data.to_string(index=False)}"
    full_prompt = f"{context}\n\nUser Prompt: {prompt}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Function to read uploaded file based on its type
def read_file(file):
    file_extension = file.name.split(".")[-1].lower()

    if file_extension == "csv":
        return pd.read_csv(file)
    elif file_extension == "xlsx":
        return pd.read_excel(file)
    elif file_extension == "json":
        return pd.json_normalize(json.load(file))
    elif file_extension == "sql":
        with sqlite3.connect(file.name) as conn:
            query = st.text_area("Enter your SQL query:")
            if query:
                return pd.read_sql_query(query, conn)
    else:
        st.error("Unsupported file format")
        return pd.DataFrame()

# Streamlit app
st.title("Syndicated Lending and Loan Structure Analysis with GPT")

# Step 1: Upload file (CSV, Excel, JSON, SQL)
st.header("Upload File for Analysis")
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json", "sql"])

# If a file is uploaded, read it based on its type
if uploaded_file:
    with st.spinner("Reading file data..."):
        loan_data = read_file(uploaded_file)
        if not loan_data.empty:
            st.write("Data uploaded successfully!")
        else:
            st.error("No data available or unable to read the file.")

# Step 2: Generate insights with Google Gemini-based analysis
st.header("Generate Loan Insights")
user_prompt = st.text_area("Enter your question or analysis prompt:", height=150)

# If both file is uploaded and user prompt is given
if uploaded_file and user_prompt:
    if not loan_data.empty:
        st.write("Data ready for analysis.")

        st.header("Generated Insights")
        with st.spinner("Generating insights with Generative AI..."):
            response_text = generate_text_with_rag(user_prompt, loan_data)
            st.write(response_text)
    else:
        st.error("No data available.")
