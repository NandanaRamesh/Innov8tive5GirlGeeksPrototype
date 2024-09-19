import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configure the Google Gemini API
api_key = "AIzaSyCSp7sJdDc84jzr_hOLqVCVWHEAOs0pvgU"
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize loan_data variable to avoid NameError
loan_data = None

# Function to generate text using Google Gemini API with RAG
def generate_text_with_rag(prompt, retrieved_data):
    context = f"Relevant information from the loan database:\n{retrieved_data.to_string(index=False)}"
    full_prompt = f"{context}\n\nUser Prompt: {prompt}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Streamlit app
st.title("Syndicated Lending and Loan Structure Analysis with GPT")

# Step 1: Upload CSV file
st.header("Upload CSV File for Analysis")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

# If a file is uploaded, read it into a DataFrame
if uploaded_file:
    with st.spinner("Reading CSV data..."):
        loan_data = pd.read_csv(uploaded_file)
        st.write("Data uploaded successfully!")

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
