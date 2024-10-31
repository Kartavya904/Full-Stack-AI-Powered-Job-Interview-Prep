

import string
import spacy
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the English NLP model from spaCy
nlp = spacy.load("en_core_web_sm")

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

# Example usage with your resume text
resume_text = """

SHIVAM KHARANGATE
(513) 908-8618 | sinayksp@mail.uc.edu | LinkedIn | GitHub | Portfolio

Education
University of Cincinnati	Cincinnati, OH
Bachelor of Science in Computer Science, Minor in Statistics	Expected Graduation: May 2027
o	Related Coursework: Programming Languages, Discrete Structures, Probability and Statistics I, Linear Algebra

Work Experience
Data Systems Researcher | IASRL Lab, University of Cincinnati, OH	   September 2024 – Present
o	Synthesized a real-time BLE vibration analysis device calibrated to detect subtle vibrations wirelessly on an autonomously rotating Control Moment Gyroscope (CMG) engine, leveraging a Nano ESP-32 microcontroller and an IMU sensor
o	Architected data acquisition pipeline with C++ and MATLAB, using FFT and Kalman Filter for mapping key vibration patterns

Machine Learning Research Co-op | National Taipei University of Technology, Taiwan	      May 2024 – August 2024                                                                                                       
o	Revamped deep learning architectures integrating novel networks by utilizing TensorFlow with Keras for passenger volume forecasting in railway transit, achieving a 15% improvement in model evaluation metric scores
o	Implemented a CNN-based image classification system for defect detection in railroad tracks, attaining an 82% test accuracy
o	Established a Variational Autoencoder model to effectively denoise sensor readings, enhancing total signal clarity by 19-24%

Embedded Systems Research Assistant | MEMS & AIM Lab, University of Cincinnati, OH	   May 2023 – February 2024
o	Instantiated a Python-based data acquisition system on a Raspberry Pi with two PMS-11 sensors modified with micropumps, applying serial communication and CRC error-checking to monitor and log particle counts 
o	Developed a web server for an ESP-32 board using C++, MicroPython, HTML, and JavaScript for a high-voltage DC circuit
o	Formulated SOPs and automated machinery for modifying PCBs, resulting in a 60% improvement in production efficiency

Skills
Programming Languages – Python, C++, C#, Java, R, SQL, Julia, Scala, JavaScript, Haskell, Swift, VBA, LabVIEW, MATLAB
Libraries & Frameworks – TensorFlow, Keras, PyTorch, HuggingFace, Scikit-learn, Pandas, Matplotlib, React, Angular, Node.js

Projects
FinVest, Future of Data Hackathon (2024) | C#, .NET, Chart.js, Plotly, ML.NET, Unity, SQL, IndexedDB	      September 2024
o	Spearheaded “FinVest”, a financial and stock dashboard enabling users to visualize connected bank transactions and real-time stock prices, with features for paper trading, sentiment analysis, and predictive insights based on historical data
o	Honored with the “Finance Best Software” award, blending VR financial comparisons with budgeting and investing analysis

Picarchu, PBL Taipei Tech Workshop (2024) | Arduino, C++, Python, PixyMon, SolidWorks	   August 2024 
o	Constructed "Picarchu," an autonomous robot vehicle capable of sorting and picking up different color cubes integrated with obstacle avoidance operating PID control, crafted with sensors, servos and 3D-printed grabbing and lifting mechanisms
o	Fine-tuned camera precision and programmed through ATmega2560 controller, leading the team into successful performance

HealthSphere, RevolutionUC Hackathon (2024) | JavaScript, Pandas, Scikit-Learn, PostgreSQL	   February 2024
o	Innovated “HealthSphere,” a health and wellness platform designed to improve the clinical trial process by integrating data-driven insights through ML and visualizations, providing personalized insights for empowering health management
o	Conferred the “Best Digital Solution to Improve the Clinical Trial Process" and "Best Use of Taipy" category accolades

FaunaFinder, MakeUC Hackathon (2023) | Python, HTML, JavaScript, Flask, Cloud Vision API	   November 2023
o	Engineered “FaunaFinder”, a web application enabling instant animal recognition through user-uploaded pictures, and also summarizing detailed information through query search on any animal, achieving an accuracy rate of 75-85%
o	Awarded the “Best Use of AI in Education” category award, highlighting proficiency in image recognition and analysis

Leadership Experience
ENED Teaching Assistant | CEAS – Engineering, University of Cincinnati, OH	                      January 2024 – Present
o	Facilitated and guided 120+ first-year students (35+ teams) in assignments, peer mentoring, tutoring, and teamwork guidance, fostering algorithmic thinking and proficiency in Python, Excel, LabVIEW, MATLAB, VBA, and Spatial Visualization
o	Innovated AI course modules for ENED as part of FYE2.0, integrating concepts of generative AI logic formation with workflows

SRS Leader and MASS Tutor | Learning Commons, University of Cincinnati, OH	   August 2024 – Present
o	Assisted in educating over 45 students in review sessions in concepts of Calculus I (MATH1061), ensuring smooth comprehension and understanding through engaging lectures, achieving 3 different awards for job professionalism
o	Provided additional one-to-one support and guidance to students in Mathematics and Science, tailoring unique study plans


                      AVAILABLE FOR CO-OP: SPRING/SUMMER 2025

"""

# Extract keywords from the resume text
keywords = extract_keywords(resume_text)

# Display extracted keywords
print("Extracted Keywords:")
for keyword, score in keywords:
    print(f"{keyword}: {score:.4f}")
