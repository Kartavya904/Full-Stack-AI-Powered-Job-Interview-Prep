from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from PyPDF2 import PdfReader
from docx import Document
from bson import ObjectId
import string
import spacy
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import random

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


# Load the English NLP model from spaCy
nlp = spacy.load("en_core_web_sm")

# Comprehensive dictionary with 5 questions for each CS-related keyword
questions_dict = {
    "algorithm": [
        "Can you describe a time you implemented an algorithm to solve a problem?",
        "How do you evaluate the efficiency of an algorithm?",
        "What are the differences between time and space complexity?",
        "How would you approach optimizing an algorithm for performance?",
        "What is your experience with recursive algorithms?"
    ],
    "data": [
        "How do you approach cleaning and organizing data for analysis?",
        "What is your experience with data visualization tools?",
        "Can you explain the importance of data integrity?",
        "Describe a time you handled large data sets in a project.",
        "How would you handle data redundancy in a database?"
    ],
    "database": [
        "What are the key differences between SQL and NoSQL databases?",
        "How do you design a relational database for scalability?",
        "What is your experience with database optimization techniques?",
        "Can you describe the process of normalizing a database?",
        "How would you approach designing a schema for a new project?"
    ],
    "sql": [
        "Explain the concept of joins in SQL and their types.",
        "How do you optimize SQL queries for performance?",
        "Describe a complex SQL query you've written.",
        "What is the purpose of indexing in SQL databases?",
        "Can you explain the differences between UNION and JOIN?"
    ],
    "java": [
        "What are the key features of Java that make it platform-independent?",
        "Can you explain the differences between abstract classes and interfaces in Java?",
        "How does Java handle memory management?",
        "Describe a Java project you've worked on and your role in it.",
        "What is your experience with Java frameworks like Spring?"
    ],
    "python": [
        "What libraries do you commonly use for data analysis in Python?",
        "Explain the concept of list comprehensions in Python.",
        "How do you handle exceptions in Python?",
        "Describe a project where you used Python for backend development.",
        "What is your experience with Python's OOP features?"
    ],
    "c++": [
        "What are the key differences between C++ and other OOP languages?",
        "Can you explain the concept of pointers in C++?",
        "How does memory management differ in C++ compared to Java?",
        "What are your strategies for debugging C++ code?",
        "Describe a project where you used C++ extensively."
    ],
    "javascript": [
        "What are closures in JavaScript, and why are they useful?",
        "Can you explain the difference between `let`, `var`, and `const`?",
        "How do you handle asynchronous operations in JavaScript?",
        "What is your experience with JavaScript frameworks like React or Vue?",
        "Describe a challenging JavaScript problem you've solved."
    ],
    "html": [
        "How do you ensure web accessibility when writing HTML?",
        "What are semantic HTML tags, and why are they important?",
        "Describe your experience with HTML5.",
        "How do you optimize HTML for SEO purposes?",
        "Can you explain the difference between block and inline elements?"
    ],
    "css": [
        "What are CSS preprocessors, and have you used any?",
        "How do you create responsive layouts with CSS?",
        "Explain the difference between Flexbox and Grid in CSS.",
        "Describe a complex design you've implemented using CSS.",
        "How do you optimize CSS for faster page load times?"
    ],
    "software": [
        "What is your experience with software development methodologies?",
        "How do you ensure quality in software you develop?",
        "Describe a time you participated in a software code review.",
        "What tools do you use for software testing?",
        "Explain the concept of version control and its importance."
    ],
    "development": [
        "How do you approach debugging during development?",
        "What are some best practices you follow in software development?",
        "Describe a challenging development problem you've solved.",
        "How do you prioritize tasks during development?",
        "What is your experience with CI/CD in development?"
    ],
    "machine": [
        "What is your experience with machine learning algorithms?",
        "Can you explain the concept of supervised vs unsupervised learning?",
        "How do you handle data preprocessing for machine learning?",
        "Describe a machine learning project you've worked on.",
        "What libraries do you use for machine learning in Python?"
    ],
    "learning": [
        "How do you choose a machine learning model for a problem?",
        "What is the role of cross-validation in model evaluation?",
        "Describe a time you improved a machine learning model’s accuracy.",
        "What are some common challenges in machine learning projects?",
        "Explain the concept of overfitting and how to prevent it."
    ],
    "network": [
        "What protocols are you familiar with for network communication?",
        "How do you ensure security in network applications?",
        "Describe a time you optimized a network application.",
        "What is your experience with socket programming?",
        "Explain the difference between TCP and UDP."
    ],
    "api": [
        "What are RESTful APIs, and how do you implement them?",
        "Describe a project where you used an external API.",
        "How do you handle API errors and exceptions?",
        "What is your experience with API authentication mechanisms?",
        "Explain the importance of rate limiting in APIs."
    ],
    # Additional keywords can be added in a similar structure...
}


# Step 1: Define a function to clean and preprocess the text
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text

# Step 2: Define CS and interview-related keywords
cs_keywords = set([
    "algorithm", "data", "structure", "database", "sql", "nosql", "java", "python", "c++", 
    "javascript", "html", "css", "software", "development", "machine", "learning", "artificial", 
    "intelligence", "deep", "neural", "network", "api", "git", "agile", "scrum", "version", 
    "control", "testing", "debugging", "cloud", "aws", "azure", "docker", "kubernetes", 
    "frontend", "backend", "full-stack", "devops", "computer", "science", "programming", 
    "interface", "system", "architecture", "performance", "scalability", "security", 
    "automation", "software", "engineering", "data", "analysis", "visualization", "model", 
    "data", "structures", "syntax", "compilation", "runtime", "exception", "memory", 
    "management", "object-oriented", "functional", "paradigm", "test", "case", "unit", 
    "integration", "deployment", "continuous", "integration", "delivery", "networking", 
    "protocol", "http", "https", "tcp", "ip", "json", "xml", "rest", "graphql", "microservices", 
    "dependency", "injection", "framework", "react", "angular", "vue", "typescript", "ruby", 
    "swift", "kotlin", "scala", "elixir", "go", "shell", "scripting", "load", "balancing", 
    "data", "warehouse", "big", "data", "hadoop", "spark", "etl", "data", "mining", "data", 
    "cleaning", "data", "engineering", "natural", "language", "processing", "computer", 
    "vision", "reinforcement", "learning", "chatbot", "modeling", "simulation", "virtualization", 
    "hypervisor", "cloud", "infrastructure", "service", "architecture", "mobile", "application", 
    "development", "cybersecurity", "incident", "response", "threat", "detection", "malware", 
    "penetration", "testing", "firewall", "encryption", "hashing", "oauth", "jwt", "tokens", 
    "user", "experience", "usability", "user", "interface", "ux", "ui", "agile", "methodologies", 
    "sdlc", "waterfall", "iterative", "prototyping", "requirements", "gathering", "specifications", 
    "documentation", "collaboration", "stakeholders", "product", "owner", "product", "manager", 
    "technical", "lead", "senior", "developer", "junior", "intern", "mentoring", "training", 
    "soft", "skills", "communication", "problem", "solving", "critical", "thinking"
])


# Step 3: Extract keywords using spaCy and TF-IDF
def extract_keywords(text):
    # Preprocess the text
    cleaned_text = preprocess_text(text)

    # Tokenize the text
    tokens = cleaned_text.split()

    # Step 4: Define a list of common stopwords to remove
    stopwords = set([
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
        "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
        "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
        "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
        "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
        "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
        "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
        "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
        "in", "out", "on", "off", "over", "under", "again", "further", "then", "once",
        "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", 
        "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", 
        "should", "now"
    ])

    # Filter out stopwords and get only relevant tokens
    relevant_tokens = [token for token in tokens if token not in stopwords]

    # Use spaCy to get parts of speech
    doc = nlp(" ".join(relevant_tokens))
    keywords = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN']]

    # Count the frequency of each keyword
    keyword_counts = Counter(keywords)

    # Use TF-IDF to rank the keywords
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([cleaned_text])
    feature_array = vectorizer.get_feature_names_out()
    
    # Sort keywords by their TF-IDF scores
    tfidf_sorting = tfidf_matrix.toarray().flatten().argsort()[::-1]

    # Combine frequency and TF-IDF for final ranking
    ranked_keywords = {}
    for idx in tfidf_sorting:
        keyword = feature_array[idx]
        if keyword in keyword_counts:
            # Weigh the keyword by its frequency and TF-IDF score
            ranked_keywords[keyword] = keyword_counts[keyword] * tfidf_matrix[0, idx]

    # Filter for only CS and interview-related keywords
    filtered_keywords = {k: v for k, v in ranked_keywords.items() if k in cs_keywords}

    # Sort by combined score
    sorted_keywords = sorted(filtered_keywords.items(), key=lambda item: item[1], reverse=True)

    return sorted_keywords


# Generate Questions Route
@app.route('/generate', methods=['POST'])
def generate_questions():
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 403

    user_id = session['user_id']
    user = login_data_collection.find_one({"_id": ObjectId(user_id)})

    # Check if the user exists in the database
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check that resumeText and coverText exist
    resume_text = user.get("resumeText")
    cover_text = user.get("coverText")
    job_description = request.form.get("job_description")

    if not resume_text or not cover_text:
        return jsonify({"error": "Resume and Cover Letter are required."}), 400

    if len(job_description.split()) < 50:
        return jsonify({"error": "Job description must be at least 50 words long."}), 400

    # Create a combined result for display
    combined_text = f"Resume Text: {resume_text}\nCover Letter Text: {cover_text}\nJob Description: {job_description}"
    extracted_keywords = extract_keywords(combined_text)
    retText = "Generated Interview Questions:\n\n"
    for keyword, score in extracted_keywords:
        if keyword in questions_dict:
            question = random.choice(questions_dict[keyword])  # Select one random question from each keyword
            retText += f"Keyword: {keyword.capitalize()}\n - {question}\n\n"

    return jsonify({"combined_text": retText})

if __name__ == '__main__':
    app.run(debug=True)
