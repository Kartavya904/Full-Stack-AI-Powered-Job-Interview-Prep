import os
import pandas as pd
from PyPDF2 import PdfReader
import string
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib  # For saving and loading the model

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Step 1: Function to extract text from resumes
def extract_text_from_resumes(folder_path):
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return pd.DataFrame()  # Return an empty DataFrame if the folder does not exist

    texts = []
    file_names = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'rb') as file:
                    reader = PdfReader(file)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text() or ''
                    texts.append(text)
                    file_names.append(filename)
            except Exception as e:
                print(f"Error reading '{file_path}': {e}")

    return pd.DataFrame({'filename': file_names, 'text': texts})


# Step 2: Function to preprocess text
def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = text.split()
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

# Step 3: Function to train the TF-IDF model and save it
def train_and_save_model(resume_data, model_filename='tfidf_vectorizer.joblib', top_n=10):
    vectorizer = TfidfVectorizer(max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform(resume_data['cleaned_text'])
    
    # Save the trained model
    joblib.dump(vectorizer, model_filename)
    print(f"Model saved as {model_filename}")
    
    return vectorizer, tfidf_matrix

# Step 4: Function to extract keywords from trained model
def extract_keywords(vectorizer, text_data, top_n=10):
    tfidf_matrix = vectorizer.transform(text_data)
    feature_names = vectorizer.get_feature_names_out()

    keywords = {}
    for idx in range(tfidf_matrix.shape[0]):
        tfidf_scores = tfidf_matrix[idx, :].toarray()[0]
        top_keywords_indices = tfidf_scores.argsort()[-top_n:][::-1]
        keywords[resume_data['filename'][idx]] = [feature_names[i] for i in top_keywords_indices]

    return keywords

# Main workflow for training
folder_path = r'C:\Users\skhar\Downloads\MakeUC-Hackathon-2024\resumes'  # Specify your folder path here
resume_data = extract_text_from_resumes(folder_path)
resume_data['cleaned_text'] = resume_data['text'].apply(preprocess_text)

# Train and save the TF-IDF model
vectorizer, tfidf_matrix = train_and_save_model(resume_data)

# Step 5: Predicting keywords from new resumes
def predict_keywords(new_resume_folder_path, model_filename='tfidf_vectorizer.joblib', top_n=10):
    # Load the trained model
    vectorizer = joblib.load(model_filename)
    
    # Extract and preprocess new resumes
    new_resume_data = extract_text_from_resumes(new_resume_folder_path)
    new_resume_data['cleaned_text'] = new_resume_data['text'].apply(preprocess_text)
    
    # Extract keywords
    keywords = extract_keywords(vectorizer, new_resume_data['cleaned_text'])
    
    # Display extracted keywords
    for filename, keyword_list in keywords.items():
        print(f"{filename}: {keyword_list}")

# Example usage for predicting keywords from a new set of resumes
new_folder_path = r'C:\Users\skhar\Downloads\MakeUC-Hackathon-2024\resumes'  # Make sure this path is correct
predict_keywords(new_folder_path)
