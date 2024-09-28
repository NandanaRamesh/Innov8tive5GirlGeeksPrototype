import streamlit as st
import pandas as pd
import google.generativeai as genai
from supabase import create_client, Client
import io
import pytesseract
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import hashlib

# Google Gemini API configuration
api_key = "AIzaSyCSp7sJdDc84jzr_hOLqVCVWHEAOs0pvgU"
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Supabase configuration
SUPABASE_URL = "https://okkgejgtoimlgwyccfcd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ra2dlamd0bGltbGd3eWNjZmNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjc0NjU3MTIsImV4cCI6MjA0MzA0MTcxMn0.IA6cSofMykF2J_REb-TRujB5QrDx0pjtbyNfEtr6a3c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Hash file content function
def hash_file(file_content):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()

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

# Function to upload file hash to Supabase
def store_file_hash_in_database(file_name, file_hash, email):
    try:
        data = {
            "file_name": file_name,
            "file_hash": file_hash,
            "email": email
        }
        response = supabase.table("FileHashes").insert(data).execute()
        st.success(f"Hash for {file_name} stored successfully in the database!")
    except Exception as e:
        st.error(f"Error storing hash: {e}")

# Modified upload function with file hashing
def upload_file_to_supabase(file, file_name, email):
    try:
        file_content = file.read()  # Read the file content as bytes
        file_hash = hash_file(file_content)  # Hash the file content

        if file_exists_in_supabase(file_name):
            st.warning(f"{file_name} already exists in Supabase. Skipping upload.")
        else:
            response = supabase.storage.from_('Files').upload(file_name, file_content)
            st.success(f"{file_name} uploaded successfully!")
        
        # Store file hash in the database after upload
        store_file_hash_in_database(file_name, file_hash, email)

    except Exception as e:
        st.error(f"Error uploading {file_name}: {e}")

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
    st.warning("You are not logged in. Your history won't be recorded and your files won't be stored in the database!")

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
        # Convert bank structure data to bytes for hashing
        bank_structure_bytes = bank_structure_data.encode('utf-8')

        # Upload and hash the bank structure file
        upload_file_to_supabase(io.BytesIO(bank_structure_bytes), "bank_structure.txt", st.session_state['user'].email)

# Chatbot-like interactive form for service selection
st.header("Service Selection")

service = st.selectbox("Choose a service to perform:", 
                       ["Loan Analysis", "Customer Insights", "Risk Assessment", "Fraud Detection", "Customer Feedback", "Locker Request"])

if service == "Customer Feedback":
    st.subheader("Provide Your Feedback")
    with st.form(key="feedback_form"):
        customer_name = st.text_input("Enter your name")
        feedback = st.text_area("Enter your feedback")
        submit_feedback = st.form_submit_button("Submit Feedback")
        if submit_feedback:
            st.success(f"Thank you for your feedback, {customer_name}!")
            # Upload feedback to Supabase or process it
            if 'user' in st.session_state:
                feedback_data = {"Customer": customer_name, "Feedback": feedback}
                # Upload or save feedback somewhere
                
elif service == "Locker Request":
    st.subheader("Request a Locker")
    with st.form(key="locker_form"):
        customer_name = st.text_input("Enter your name")
        locker_size = st.selectbox("Select locker size", ["Small", "Medium", "Large"])
        locker_reason = st.text_area("Reason for locker request")
        submit_locker = st.form_submit_button("Submit Request")
        if submit_locker:
            st.success(f"Locker request submitted, {customer_name}!")
            # Process or upload the locker request
            if 'user' in st.session_state:
                locker_request_data = {"Customer": customer_name, "Locker Size": locker_size, "Reason": locker_reason}
                # Upload or save locker request

elif service == "Fraud Detection":
    # Load a simple spam detection model (replace this with your actual model)
    def load_spam_model():
        vectorizer = TfidfVectorizer()
        clf = MultinomialNB()

        # Sample training data for spam detection (replace with more robust data)
        spam_data = pd.DataFrame({
            "text": [
                "You won a prize", "Claim your reward", "Important bank message",
                "Buy now", "Low interest loan"
            ],
            "label": [1, 1, 0, 1, 0]  # 1 = spam, 0 = not spam
        })
        
        X = vectorizer.fit_transform(spam_data['text'])
        y = spam_data['label']
        clf.fit(X, y)
        return vectorizer, clf

    vectorizer, spam_model = load_spam_model()

    # Function to detect spam in text
    def detect_spam(text):
        processed_text = vectorizer.transform([text])
        prediction = spam_model.predict(processed_text)
        return prediction[0]  # Returns 1 if spam, 0 if not

    # Function to extract text from an image using OCR (Tesseract)
    def extract_text_from_image(image):
        text = pytesseract.image_to_string(image)
        return text

    # Function to upload fraud complaint to Supabase
    def lodge_complaint(message, email, complaint_type="Fraud Detection"):
        try:
            data = {
                "email": email,
                "message": message,
                "complaint_type": complaint_type,
            }
            response = supabase.table("Complaints").insert(data).execute()
            st.success("Complaint lodged successfully!")
        except Exception as e:
            st.error(f"Failed to lodge complaint: {e}")

    # UI for Fraud Detection Service
    st.title("Fraud Detection System")

    # Allow users to upload an image or copy-paste text message
    fraud_detection_mode = st.selectbox("Select Mode", ["Upload Image", "Enter Text"])
    message = None

    if fraud_detection_mode == "Upload Image":
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            message = extract_text_from_image(image)
            st.write(f"Extracted Text: {message}")
    elif fraud_detection_mode == "Enter Text":
        message = st.text_area("Enter the suspicious message")

    if message:
        prediction = detect_spam(message)
        if prediction == 1:
            st.error("This message is classified as SPAM. Potential fraud detected.")
            if st.button("Lodge Complaint"):
                lodge_complaint(message, email)
        else:
            st.success("This message is classified as SAFE. No fraud detected.")
