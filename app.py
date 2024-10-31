from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from PyPDF2 import PdfReader
from docx import Document
from bson import ObjectId
from collections import Counter
import string
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
import os
from NLP_Model.nlp import *

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Configuration
uri = "mongodb+srv://kartavyasingh17:aRduRaLkLvV5zumt@resumedrive.hwagf.mongodb.net/?retryWrites=true&w=majority&appName=ResumeDrive"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["ResumeDriveDB"]
login_data_collection = db["loginData"]

# Utility functions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            return "".join([page.extract_text() for page in reader.pages]).strip()
    elif file_path.endswith('.docx'):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    else:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
# Routes
@app.route('/')
@app.route('/home')
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access the dashboard.")
        return redirect(url_for("home"))
    
    user = login_data_collection.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("dashboard.html", user=user)

@app.route('/signup', methods=['POST'])
def signup():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")

    existing_user = login_data_collection.find_one({"email": email})
    
    if existing_user:
        flash("Email already exists. Please try a different one.")
        return redirect(url_for("home"))
    
    hashed_password = generate_password_hash(password)
    login_data_collection.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password,
        "resumeName": "",
        "resumeText": "",
        "coverName": "",
        "coverText": "",
        "otherName": "",
        "otherText": "",
        "resumeKeywords": {}
    })
    
    flash("Sign up successful! You can now log in.")
    return redirect(url_for("home"))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    
    user = login_data_collection.find_one({"email": email})
    
    if user and check_password_hash(user["password"], password):
        session['user_id'] = str(user["_id"])
        session['first_name'] = user["first_name"]
        session['last_name'] = user["last_name"]
        flash("Login successful!")
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid email or password.")
        return redirect(url_for("home"))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))

# Route for Profile Page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user_id" not in session:
        flash("Please log in to access your profile.")
        return redirect(url_for("home"))

    user_id = session['user_id']
    user = login_data_collection.find_one({"_id": ObjectId(user_id)})

    if request.method == 'POST':
        # Edit Profile Logic
        if 'first_name' in request.form:
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            login_data_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {
                "first_name": first_name, "last_name": last_name
            }})
            flash("Profile updated successfully.")
        
        # Update Password Logic
        elif 'current_password' in request.form:
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            if check_password_hash(user["password"], current_password):
                login_data_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {
                    "password": generate_password_hash(new_password)
                }})
                session.clear()
                flash("Password updated successfully. Please log in again.")
                return redirect(url_for("home"))
            else:
                flash("Incorrect current password.")

        # Replace Document Logic
        elif 'replace_document' in request.form:
            replace_document = request.form.get("replace_document")
            file = request.files.get("file")
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)
            text = extract_text_from_file(file_path)  # Assuming a utility function
            nlp = load_model()
            if not Path(MODEL_PATH).exists():
                # If the model does not exist, you may need to train it first
                example_files = [file_path]  # Train on this example file (can be expanded)
                examples = generate_training_data(example_files)
                nlp = train_model(nlp, examples)

            # Extract CS-related keywords using the trained model
            extracted_keywords = extract_keywords(nlp, text)
            update_data = {}
            if replace_document == "resume":
                update_data = {"resumeName": file.filename, "resumeText": text, "resumeKeywords": extracted_keywords}
            elif replace_document == "cover":
                update_data = {"coverName": file.filename, "coverText": text}
            elif replace_document == "other":
                update_data = {"otherName": file.filename, "otherText": text}

            login_data_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
            flash(f"{replace_document.capitalize()} updated successfully.")

    return render_template('profile.html', user=user)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if "user_id" not in session:
        flash("Please log in to delete your account.")
        return redirect(url_for("home"))
    
    user_id = session['user_id']
    
    # Delete the user from the database
    login_data_collection.delete_one({"_id": ObjectId(user_id)})
    
    # Clear session and redirect to home
    session.clear()
    flash("Your account has been deleted successfully.")
    return redirect(url_for("home"))

@app.route('/upload', methods=['POST'])
def upload_files():
    if "user_id" not in session:
        return jsonify({"error": "Please log in to upload files."}), 403

    upload_type = request.form.get("upload_type")
    file = request.files.get("file")
    
    if upload_type not in ["resume", "cover", "other"] or not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid upload type or file"}), 400

    file_path = os.path.join("uploads", file.filename)
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    file.save(file_path)

    file_text = extract_text_from_file(file_path)
    nlp = load_model()
    if not Path(MODEL_PATH).exists():
        # If the model does not exist, you may need to train it first
        example_files = [file_path]  # Train on this example file (can be expanded)
        examples = generate_training_data(example_files)
        nlp = train_model(nlp, examples)

    # Extract CS-related keywords using the trained model
    extracted_keywords = extract_keywords(nlp, file_text)

    # Prepare data to update in the database
    update_data = {
        "resumeName": file.filename if upload_type == "resume" else "",
        "resumeText": file_text if upload_type == "resume" else "",
        "resumeKeywords": extracted_keywords if upload_type == "resume" else {}
    }

    # Update the user's data in MongoDB
    login_data_collection.update_one({"_id": ObjectId(session["user_id"])}, {"$set": update_data})

    return jsonify({"success": True, "message": f"{upload_type.capitalize()} uploaded successfully."})

@app.route('/generate', methods=['POST'])
def generate_keywords():
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 403

    user_id = session['user_id']
    user = login_data_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    resume_text = user.get("resumeText")
    cover_text = user.get("coverText")
    job_description = request.form.get("job_description")
    extracted_keywords = user.get("resumeKeywords", {})

    if not resume_text or not cover_text:
        return jsonify({"error": "Resume and Cover Letter are required."}), 400

    if len(job_description.split()) < 50:
        return jsonify({"error": "Job description must be at least 50 words long."}), 400
    
    # Check if there are any keywords in the database for this user
    if not extracted_keywords:
        return jsonify({"error": "No extracted keywords found for the resume. Please Re-Upload your Resume"}), 400


    combined_text = f"{resume_text}\n{cover_text}\n{job_description}"
    # Format extracted keywords for display in retText
    retText = "Extracted Keywords:\n\n"
    for keyword, count in extracted_keywords.items():
        retText += f"Keyword: {keyword.capitalize()}, Count: {count}\n"

    return jsonify({"combined_text": retText})

if __name__ == '__main__':
    app.run(debug=True)
