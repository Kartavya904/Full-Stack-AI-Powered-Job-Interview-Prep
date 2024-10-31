
import os
from flask import Flask, request, jsonify, render_template
from PyPDF2 import PdfReader
from docx import Document
import openai

# Initialize the Flask app
app = Flask(__name__)

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

  # Replace with your OpenAI API key

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to process uploaded documents
def process_uploaded_documents(resume_path, job_description_path):
    def read_pdf(file_path):
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            text = "".join([page.extract_text() for page in reader.pages])
        return text.strip()

    def read_docx(file_path):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()

    # Process resume
    resume_text = ""
    if resume_path.endswith('.pdf'):
        resume_text = read_pdf(resume_path)
    elif resume_path.endswith('.docx'):
        resume_text = read_docx(resume_path)
    else:
        with open(resume_path, 'r', encoding='utf-8') as file:
            resume_text = file.read()

    # Process job description
    job_description_text = ""
    if job_description_path.endswith('.pdf'):
        job_description_text = read_pdf(job_description_path)
    elif job_description_path.endswith('.docx'):
        job_description_text = read_docx(job_description_path)
    else:
        with open(job_description_path, 'r', encoding='utf-8') as file:
            job_description_text = file.read()

    return resume_text, job_description_text

# AI-Based Question Generation using OpenAI's API
def generate_interview_questions(resume_text, job_description_text):
    # Construct the prompt for OpenAI
    print(resume_text) #for debugging
    print(job_description_text) #for debugging

    #this will process keywords from the resume and job description to generate questions
    prompt = (
        f"Based on the following resume:\n\nhi\n\n"
        f"And the following job description:\n\nhi\n\n"
        "Generate a list of specific interview questions that would be relevant for the candidate."
    )
    
    # Call OpenAI's API to generate questions
    print(prompt) #for debugging
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )

        
    questions = response['choices'][0]['text'].strip().split("\n")
    return questions

# Route for Home Page
@app.route('/')
@app.route('/home')
def home():
    return render_template('upload.html')

# Route for document upload and processing
@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'resume' not in request.files or 'job_description' not in request.files:
            return jsonify({"error": "No file part"}), 400

        resume_file = request.files['resume']
        job_description_file = request.files['job_description']

        if not allowed_file(resume_file.filename) or not allowed_file(job_description_file.filename):
            return jsonify({"error": "Invalid file type"}), 400

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
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
