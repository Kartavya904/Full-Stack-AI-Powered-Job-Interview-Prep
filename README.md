# AI-Powered Job Interview Prep Assistant

## Overview
This project is designed to assist job seekers by generating interview questions based on the job description and user-provided documents (resume, cover letter). It also evaluates answers using Natural Language Processing (NLP) and provides feedback on clarity, confidence, and relevance. The platform suggests ideal answers based on the user’s documents and industry trends.

## Features
- **User Authentication:** Login/Sign-up system with MongoDB for user data storage.
- **Job Description Input:** Users can either paste a job description or provide a link to the job posting.
- **Resume & Document Upload:** Users can upload their resume, cover letter, and other documents.
- **AI-Based Question Generation:** Generates interview questions based on the user’s resume and job description.
- **NLP-Powered Answer Evaluation:** Provides feedback on the clarity, confidence, and relevance of user-provided answers.
- **Sample Answers:** Generates potential answers based on the uploaded documents.

## Tech Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, JavaScript (React optional for interactive UIs)
- **Database:** MongoDB (for storing user data, resumes, and job descriptions)
- **NLP:** Hugging Face's BERT (for question generation and answer evaluation)

## How it Works
- **User Sign-Up/Login:** Users create an account or log in. All data is securely saved in MongoDB.
- **Job Description Upload:** Users paste the job description or upload the link to a job posting.
- **Resume & Document Upload:** Users upload their resume, cover letter, and other documents.
- **Question Generation:** Based on the documents and job description, the platform generates interview questions tailored to the user’s experience and the position.
- **Answer Feedback:** Users can practice their responses, which are evaluated by an AI model, and receive feedback.
- **Suggested Answers:** The platform generates an optimal answer based on the user’s documents for each question.

## Requirements
- Python 3.8+
- Flask
- MongoDB
- Hugging Face Transformers Library (for NLP)
- React (optional for a dynamic frontend)
- HTML, CSS, JavaScript (for frontend if not using React)
