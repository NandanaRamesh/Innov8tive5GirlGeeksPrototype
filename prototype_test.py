import streamlit as st
import pandas as pd
import google.generativeai as genai

# Google Gemini API configuration
api_key = "AIzaSyCSp7sJdDc84jzr_hOLqVCVWHEAOs0pvgU"
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

loan_data_list = []
bank_structure_data = ""

# Function to generate text with RAG (Retrieve and Generate) model
def generate_text_with_rag(prompt, retrieved_data, structure_context):
    context = f"Bank structure:\n{structure_context}\n\nRelevant information from the loan database:\n{retrieved_data.to_string(index=False)}"
    full_prompt = f"{context}\n\nUser Prompt: {prompt}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Title and headers
st.markdown("<h1 style='text-align: center;'>GENFI-AI</h1>", unsafe_allow_html=True)
st.header("Upload Bank Structure File")

# Upload bank structure file (TXT format)
bank_structure_file = st.file_uploader("Upload Bank Structure (.txt)", type=["txt"])
if bank_structure_file:
    bank_structure_data = bank_structure_file.read().decode('utf-8')  # Read the file content but don't display
    st.success("Bank structure file uploaded successfully!")

# Upload loan files
st.header("Upload Loan Files for Analysis")
uploaded_files = st.file_uploader("Choose files", type=["csv", "json", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Reading {uploaded_file.name}..."):
            if uploaded_file.type == "text/csv":
                loan_data = pd.read_csv(uploaded_file)
            elif uploaded_file.type == "application/json":
                loan_data = pd.read_json(uploaded_file)
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        "application/vnd.ms-excel"]:
                loan_data = pd.read_excel(uploaded_file)
            else:
                st.error(f"Unsupported file type: {uploaded_file.type}")
                continue

            st.write(f"Data from {uploaded_file.name} uploaded successfully!")
            loan_data_list.append(loan_data)
            st.subheader(f"Uploaded Data from {uploaded_file.name}")
            st.dataframe(loan_data)

# User prompt for generating insights
st.header("Generate Loan Insights")
user_prompt = st.text_area("Enter your question or analysis prompt:", height=150)

# Check if loan data and user prompt are available for analysis
if uploaded_files and user_prompt:
    combined_loan_data = pd.concat(loan_data_list, ignore_index=True)

    if not combined_loan_data.empty:
        st.write("Data ready for analysis.")

        st.header("Generated Insights")
        with st.spinner("Generating insights with Generative AI..."):
            response_text = generate_text_with_rag(user_prompt, combined_loan_data, bank_structure_data)
            st.write(response_text)
    else:
        st.error("No data available.")
