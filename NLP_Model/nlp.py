import os
import re
import spacy
from spacy.training import Example
from spacy.util import minibatch
from PyPDF2 import PdfReader
from pathlib import Path

# Comprehensive list of CS-related keywords
cs_keywords = [
    # Programming Languages
    "Python", "Java", "C++", "C", "JavaScript", "Ruby", "Go", "R", "Swift", "Kotlin", "TypeScript", "Perl", "Scala", "Haskell", "Rust", "MATLAB", "Julia",

    # Frameworks and Libraries
    "Django", "Flask", "React", "Angular", "Vue", "Bootstrap", "Spring", "Hibernate", "Express", "Node.js", "TensorFlow", "PyTorch", "Keras", "Scikit-Learn",

    # Databases and Data Management
    "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Oracle", "SQLite", "Redis", "Firebase", "Elasticsearch", "BigQuery", "Cassandra",

    # Cloud Platforms and DevOps
    "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins", "Ansible", "Terraform", "CI/CD", "DevOps", "GitLab", "GitHub", "CircleCI",

    # Data Science and Machine Learning
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP", "Natural Language Processing", "Computer Vision", "Data Analysis", "Data Mining", "Data Engineering",
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly", "Statistical Modeling", "Clustering", "Regression", "Classification",

    # Software Development and Engineering Concepts
    "Object-Oriented Programming", "OOP", "Functional Programming", "Microservices", "REST API", "GraphQL", "Agile", "Scrum", "Kanban", "TDD", "Test-Driven Development",
    "BDD", "Behavior-Driven Development", "UML", "Design Patterns", "System Design", "Algorithms", "Data Structures", "Multithreading", "Concurrency", "Parallel Processing",

    # Security and Networking
    "Cybersecurity", "Penetration Testing", "Information Security", "Network Security", "Cryptography", "Firewalls", "VPN", "SSO", "OAuth", "IAM", "Public Key Infrastructure",

    # Operating Systems and Hardware
    "Linux", "Unix", "Windows", "macOS", "Embedded Systems", "Real-Time Systems", "ARM", "Raspberry Pi", "Arduino", "IoT", "Internet of Things",

    # Tools and Other Technologies
    "VSCode", "IntelliJ", "Eclipse", "NetBeans", "Vim", "Emacs", "Jupyter Notebook", "Sublime Text", "Xcode", "Android Studio", "Postman", "Figma", "Sketch", "Photoshop",
    "Tableau", "Power BI", "SAP", "Salesforce", "Jira", "Confluence", "Slack", "Microsoft Teams", "Trello", "Asana"
]

# Utility functions to check file extensions and extract text
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            return "".join([page.extract_text() for page in reader.pages]).strip()
    elif file_path.endswith('.docx'):
        from docx import Document
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs]).strip()
    else:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()

# Model paths
MODEL_PATH = 'nlpModel/spacy_cs_model'

def load_model():
    """Load a saved model if exists; otherwise, create a blank model."""
    if Path(MODEL_PATH).exists():
        nlp = spacy.load(MODEL_PATH)
        print("Loaded saved model.")
    else:
        nlp = spacy.blank("en")
        print("Created new model.")
    return nlp

def save_model(nlp):
    """Save the model to disk."""
    model_dir = Path(MODEL_PATH)
    model_dir.parent.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(MODEL_PATH)
    print("Model saved.")

def generate_training_data(file_paths):
    """Generate training data with CS keyword annotations."""
    examples = []
    for file_path in file_paths:
        text = extract_text_from_file(file_path)
        annotations = {"entities": []}
        for keyword in cs_keywords:
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                start, end = match.span()
                annotations["entities"].append((start, end, "CS_KEYWORD"))
        if annotations["entities"]:
            examples.append((text, annotations))
    return examples

def train_model(nlp, examples, n_iter=20):
    """Train the spaCy NER model with provided examples."""
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")
    
    # Add labels to the NER model
    ner.add_label("CS_KEYWORD")

    # Convert examples into spaCy's training format
    training_data = [Example.from_dict(nlp.make_doc(text), annotations) for text, annotations in examples]

    # Training loop
    optimizer = nlp.begin_training()
    for i in range(n_iter):
        losses = {}
        batches = minibatch(training_data, size=2)
        for batch in batches:
            nlp.update(batch, sgd=optimizer, losses=losses)
        print(f"Iteration {i+1}, Losses: {losses}")
    
    save_model(nlp)
    return nlp

def extract_keywords(nlp, text):
    """Extract keywords using the trained model."""
    doc = nlp(text)
    keywords = [ent.text for ent in doc.ents if ent.label_ == "CS_KEYWORD"]
    keyword_counts = {kw: keywords.count(kw) for kw in set(keywords)}
    return keyword_counts

def process_resumes(resume_folder):
    """Process resumes, extract text, and apply the trained model for keyword extraction."""
    resume_texts = []
    file_names = []

    # Gather resume texts for training
    for file_name in os.listdir(resume_folder):
        file_path = os.path.join(resume_folder, file_name)
        if allowed_file(file_name):
            text = extract_text_from_file(file_path)
            resume_texts.append(text)
            file_names.append(file_name)

    # Load or train the model
    nlp = load_model()
    if not Path(MODEL_PATH).exists():
        examples = generate_training_data([os.path.join(resume_folder, fname) for fname in file_names])
        nlp = train_model(nlp, examples)

    # Use the model to extract keywords from each resume
    for file_name, text in zip(file_names, resume_texts):
        cs_keywords_found = extract_keywords(nlp, text)
        print(f"Keywords for {file_name}: {cs_keywords_found}")

# Define the path to your resume folder
resume_folder_path = 'NLP_Model/resumes'
process_resumes(resume_folder_path)
