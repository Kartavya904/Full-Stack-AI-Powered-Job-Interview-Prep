##AI-Powered Job Interview Prep Assistant
#Overview
This project is designed to assist job seekers by generating interview questions based on the job description and user-provided documents (resume, cover letter). It also evaluates answers using Natural Language Processing (NLP) and provides feedback on clarity, confidence, and relevance. The platform suggests ideal answers based on the user’s documents and industry trends.

#Features
<strong>User Authentication:</strong> Login/Sign-up system with MongoDB for user data storage.
<strong>Job Description Input:</strong> Users can either paste a job description or provide a link to the job posting.
<strong>Resume & Document Upload:</strong> Users can upload their resume, cover letter, and other documents.
<strong>AI-Based Question Generation:</strong> Generates interview questions based on the user’s resume and job description.
<strong>NLP-Powered Answer Evaluation:</strong> Provides feedback on the clarity, confidence, and relevance of user-provided answers.
<strong>Sample Answers:</strong> Generates potential answers based on the uploaded documents.

#Tech Stack
<strong>Backend:</strong> Flask (Python)
<strong>Frontend:</strong> HTML, CSS, JavaScript (React optional for interactive UIs)
<strong>Database:</strong> MongoDB (for storing user data, resumes, and job descriptions)
<strong>NLP:</strong> Hugging Face's BERT (for question generation and answer evaluation)

#How it Works
<strong>User Sign-Up/Login:</strong> Users create an account or log in. All data is securely saved in MongoDB.
<strong>Job Description Upload:</strong> Users paste the job description or upload the link to a job posting.
<strong>Resume & Document Upload:</strong> Users upload their resume, cover letter, and other documents.
<strong>Question Generation:</strong> Based on the documents and job description, the platform generates interview questions tailored to the user’s experience and the position.
<strong>Answer Feedback:</strong> Users can practice their responses, which are evaluated by an AI model, and receive feedback.
<strong>Suggested Answers:</strong> The platform generates an optimal answer based on the user’s documents for each question.

#Requirements
Python 3.8+
Flask
MongoDB
Hugging Face Transformers Library (for NLP)
React (optional for a dynamic frontend)
HTML, CSS, JavaScript (for frontend if not using React)