import streamlit as st
import pandas as pd
import google.generativeai as genai
from supabase import create_client, Client
import io

# Google Gemini API configuration
api_key = "AIzaSyCSp7sJdDc84jzr_hOLqVCVWHEAOs0pvgU"
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Supabase configuration
SUPABASE_URL = "https://okkgejgtoimlgwyccfcd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ra2dlamd0b2ltbGd3eWNjZmNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjc0NjU3MTIsImV4cCI6MjA0MzA0MTcxMn0.IA6cSofMykF2J_REb-TRujB5QrDx0pjtbyNfEtr6a3c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# User login with Supabase
def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.success(f"Logged in as {response.user.email}")
        return response.user
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None

# User signup with Supabase
def sign_up_user(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        st.success(f"Account created for {response.user.email}")
        return response.user
    except Exception as e:
        st.error(f"Signup failed: {e}")
        return None

# Function to check if file exists in Supabase Storage
def file_exists_in_supabase(file_name):
    try:
        response = supabase.storage.from_('Files').list()
        existing_files = [file['name'] for file in response]
        return file_name in existing_files
    except Exception as e:
        st.error(f"Error checking file existence: {e}")
        return False

# Modified upload function
def upload_file_to_supabase(file, file_name):
    try:
        if file_exists_in_supabase(file_name):
            st.warning(f"{file_name} already exists in Supabase. Skipping upload.")
        else:
            file_content = file.read()  # Read the file content as bytes
            response = supabase.storage.from_('Files').upload(file_name, file_content)
            st.success(f"{file_name} uploaded successfully!")
    except Exception as e:
        st.error(f"Error uploading {file_name}: {e}")

# Function to retrieve file from Supabase
def download_file_from_supabase(file_name):
    try:
        response = supabase.storage().from_('documents').download(file_name)
        return response
    except Exception as e:
        st.error(f"Error downloading {file_name}: {e}")
        return None

# Function to generate text with RAG (Retrieve and Generate) model
def generate_text_with_rag(prompt, retrieved_data, structure_context):
    context = f"Bank structure:\n{structure_context}\n\nRelevant information from the loan database:\n{retrieved_data.to_string(index=False)}"
    full_prompt = f"{context}\n\nUser Prompt: {prompt}"

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# UI for authentication
st.sidebar.title("User Authentication")

# Toggle between Login and Signup
auth_choice = st.sidebar.radio("Choose Action", ["Login", "Sign Up"])

email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if auth_choice == "Login":
    if st.sidebar.button("Login"):
        user = login_user(email, password)
        if user:
            st.session_state['user'] = user  # Store user object in session state
elif auth_choice == "Sign Up":
    if st.sidebar.button("Sign Up"):
        user = sign_up_user(email, password)
        if user:
            st.session_state['user'] = user  # Store user object in session state

# Check if the user is logged in
if 'user' in st.session_state:
    st.success(f"Welcome {st.session_state['user'].email}")  # Access user email with dot notation
    allow_upload_to_supabase = True
else:
    st.warning("You are not logged in. Your history wont be recorded and your files wont be stored in the database!")

# Title and headers
st.markdown("<h1 style='text-align: center;'>GENFI-AI</h1>", unsafe_allow_html=True)
st.header("Upload Bank Structure File")

# Upload bank structure file (TXT format)
bank_structure_file = st.file_uploader("Upload Bank Structure (.txt)", type=["txt"])
if bank_structure_file:
    bank_structure_data = bank_structure_file.read().decode('utf-8')
    st.success("Bank structure file uploaded successfully!")
    # Upload only if logged in
    if 'user' in st.session_state:
        upload_file_to_supabase(io.BytesIO(bank_structure_data.encode()), "bank_structure.txt")

# Upload loan files
st.header("Upload Loan Files for Analysis")
uploaded_files = st.file_uploader("Choose files", type=["csv", "json", "xlsx"], accept_multiple_files=True)

loan_data_list = []

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

            # Upload the loan data file to Supabase only if logged in
            if 'user' in st.session_state:
                upload_file_to_supabase(uploaded_file, uploaded_file.name)

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
