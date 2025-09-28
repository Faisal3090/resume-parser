import streamlit as st
import os
import pandas as pd
import re
import spacy
from pypdf import PdfReader
from docx import Document

# Load spaCy model (works on Streamlit Cloud too)
import en_core_web_sm
nlp = en_core_web_sm.load()

def extract_text(file):
    text = ""
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)  
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:  
                text += page_text + "\n"
    elif file.name.endswith('.docx'):
        doc = Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        raise ValueError("Unsupported file format")
    return text

def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def extract_emails(text):
    match = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match if match else None

def extract_phones(text):
    match = re.search(r'(\+91[\s-]?\d{5}[\s-]?\d{5}|\d{10})', text)
    return match.group(0) if match else None

def extract_name(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            return ent.text
    return None

SKILLS = ['Python', 'Java', 'C++', 'Machine Learning', 'Data Analysis', 'SQL', 'Excel', 'Communication', 'Leadership']
def extract_skills(text, skills=SKILLS):
    found = [skill for skill in skills if skill.lower() in text.lower()]
    return list(set(found))

EDU_KEYWORDS = ['B.Tech', 'M.Tech', 'B.Sc', 'M.Sc', 'PhD', 'Bachelor', 'Master', 'University', 'College', 'School', 'Degree']
def extract_education(text):
    lines = text.split('\n')
    education = []
    for i, line in enumerate(lines):
        for word in EDU_KEYWORDS:
            if word.lower() in line.lower():
                education.append(line.strip())
                if i + 1 < len(lines) and lines[i+1].strip():
                    education.append(lines[i+1].strip())
                break
    return sorted(set(education))

def extract_experience(text):
    experience_keywords = ['experience', 'worked', 'employment', 'career', 'professional']
    exp_set = set()
    lines = text.split('\n')
    for line in lines:
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in experience_keywords):
            exp_set.add(line.strip())
    return list(exp_set)


st.title("Resume Parser App")

# Allow multiple file upload (PDFs or DOCX)
uploaded_files = st.file_uploader(
    "Drag and drop resumes here or click to select files:",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if st.button("Parse Resumes"):
    if uploaded_files:
        results = []
        for file in uploaded_files:
            text = clean_text(extract_text(file))
            parsed = {
               "File": file.name,
               "Name": extract_name(text),
               "Email": extract_emails(text),
               "Phone": extract_phones(text),
               "Skills": extract_skills(text),
               "Education": extract_education(text),
               "Experience": extract_experience(text)  
            }
            results.append(parsed)

        df = pd.DataFrame(results)
        st.success(f"Parsed {len(df)} resumes!")
        st.dataframe(df)

# Download button for CSV
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Parsed Resumes as CSV",
            data=csv_data,
            file_name="prased_resumes.csv",
            mime='text/csv'
        )
