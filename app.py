from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from PyPDF2 import PdfReader
from docx import Document
from bson import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Configuration
uri = "mongodb+srv://kartavyasingh17:aRduRaLkLvV5zumt@resumedrive.hwagf.mongodb.net/?retryWrites=true&w=majority&appName=ResumeDrive"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["ResumeDriveDB"]
login_data_collection = db["loginData"]

# Route for Home Page
@app.route('/')
@app.route('/home')
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))  # Redirect to /dashboard if logged in
    return render_template('home.html')

# Dashboard Route
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        flash("Please log in to access the dashboard.")
        return redirect(url_for("home"))
    
    user = login_data_collection.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("dashboard.html", user=user)

# Signup Route
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
        "otherText": ""
    })
    
    flash("Sign up successful! You can now log in.")
    return redirect(url_for("home"))

# Login Route
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

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))

# Utility to check allowed file types
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Utility to process documents
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

# Route for Profile Page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "user_id" not in session:
        flash("Please log in to access your profile.")
        return redirect(url_for("home"))
    
    user_id = session['user_id']
    user = login_data_collection.find_one({"_id": user_id})

    if request.method == 'POST':
        # Update user data in MongoDB
        login_data_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "email": request.form.get("email")
            }}
        )
        flash("Profile updated successfully.")
        return redirect(url_for("profile"))

    return render_template('profile.html', user=user)

# Upload documents route
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

    update_data = {}
    if upload_type == "resume":
        update_data = {"resumeName": file.filename, "resumeText": file_text}
    elif upload_type == "cover":
        update_data = {"coverName": file.filename, "coverText": file_text}
    elif upload_type == "other":
        update_data = {"otherName": file.filename, "otherText": file_text}

    login_data_collection.update_one({"_id": ObjectId(session["user_id"])}, {"$set": update_data})

    return jsonify({"success": True, "message": f"{upload_type.capitalize()} uploaded successfully."})

if __name__ == '__main__':
    app.run(debug=True)
