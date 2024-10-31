from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages

# MongoDB Configuration
uri = "mongodb+srv://kartavyasingh17:aRduRaLkLvV5zumt@resumedrive.hwagf.mongodb.net/?retryWrites=true&w=majority&appName=ResumeDrive"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["ResumeDriveDB"]
login_data_collection = db["loginData"]

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

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
    
    user = {
        "first_name": session.get("first_name"),
        "last_name": session.get("last_name")
    }
    return render_template("dashboard.html", user=user)

# Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")

    # Check if the email already exists in the database
    existing_user = login_data_collection.find_one({"email": email})
    
    if existing_user:
        flash("Email already exists. Please try a different one.")
        return redirect(url_for("home"))
    
    # Hash the password for security
    hashed_password = generate_password_hash(password)

    # Insert new user data into MongoDB
    login_data_collection.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password
    })
    
    flash("Sign up successful! You can now log in.")
    return redirect(url_for("home"))

# Login Route
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    
    # Find user by email
    user = login_data_collection.find_one({"email": email})
    
    if user and check_password_hash(user["password"], password):
        # Store user information in session
        session['user_id'] = str(user["_id"])
        session['first_name'] = user["first_name"]
        session['last_name'] = user["last_name"]
        flash("Login successful!")
        return redirect(url_for("dashboard"))  # Redirect to /dashboard
    else:
        flash("Invalid email or password.")
        return redirect(url_for("home"))

# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out.")
    return redirect(url_for("home"))

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

if __name__ == '__main__':
    app.run(debug=True)
