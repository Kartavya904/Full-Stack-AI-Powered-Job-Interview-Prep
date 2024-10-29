import os
from flask import Flask, request, jsonify, render_template
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline
from PyPDF2 import PdfReader
from docx import Document

# Initialize the Flask app
app = Flask(__name__)

# Route for Home Page
@app.route('/')
@app.route('/home')
def home():
    return render_template('upload.html')

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the model and tokenizer
model_name = "gpt2"  # Use "gpt-4" if you have access to the API
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to process uploaded documents
def process_uploaded_documents(resume_path, job_description_path):
    resume_text = ""
    job_description_text = ""

    # Function to read PDF files
    def read_pdf(file_path):
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()

    # Function to read DOCX files
    def read_docx(file_path):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()

    # Read resume
    if resume_path.endswith('.pdf'):
        resume_text = read_pdf(resume_path)
    elif resume_path.endswith('.docx'):
        resume_text = read_docx(resume_path)
    else:
        with open(resume_path, 'r', encoding='utf-8') as file:
            resume_text = file.read()

    # Read job description if provided
    if job_description_path:
        if job_description_path.endswith('.pdf'):
            job_description_text = read_pdf(job_description_path)
        elif job_description_path.endswith('.docx'):
            job_description_text = read_docx(job_description_path)
        else:
            with open(job_description_path, 'r', encoding='utf-8') as file:
                job_description_text = file.read()

    return resume_text, job_description_text


# AI-Based Question Generation
def generate_interview_questions(resume_text, job_description_text):
    input_text = f"Based on this resume:\n{resume_text}\nand this job description:\n{job_description_text}\n, generate interview questions."
    
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_length=512)
    questions = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # After processing the documents
    print(f"Resume Text: {resume_text[:1000]}")  # Print first 1000 characters for debugging
    print(f"Job Description Text: {job_description_text[:1000]}")  # Print first 1000 characters for debugging

    return questions

# NLP-Powered Answer Evaluation
def evaluate_answer(answer, question):
    # Use a simple sentiment analysis model for demo purposes
    evaluation_pipeline = pipeline("sentiment-analysis")
    input_text = f"Question: {question}\nAnswer: {answer}"
    feedback = evaluation_pipeline(input_text)
    
    return feedback

# Suggested Answers Generation
def generate_suggested_answers(resume_text, job_description_text, question):
    input_text = f"Based on the resume:\n{resume_text}\nand job description:\n{job_description_text},\nanswer the following question: {question}"
    
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_length=512)
    suggested_answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return suggested_answer

# Route for document upload and processing
@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'resume' not in request.files or 'job_description' not in request.files:
            return jsonify({"error": "No file part"}), 400

        resume_file = request.files['resume']
        job_description_file = request.files['job_description']

        if resume_file.filename == '' or not allowed_file(resume_file.filename):
            return jsonify({"error": "Invalid resume file"}), 400

        if job_description_file.filename == '' or not allowed_file(job_description_file.filename):
            return jsonify({"error": "Invalid job description file"}), 400

        # Save uploaded files
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
        job_description_path = os.path.join(app.config['UPLOAD_FOLDER'], job_description_file.filename)

        resume_file.save(resume_path)
        job_description_file.save(job_description_path)

        # Process the uploaded documents
        resume_text, job_description_text = process_uploaded_documents(resume_path, job_description_path)

        # Generate questions based on the documents
        questions = generate_interview_questions(resume_text, job_description_text)

        return jsonify({"questions": questions})

    except Exception as e:
        print(f"Error: {e}")  # Print the exception details to the console
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
