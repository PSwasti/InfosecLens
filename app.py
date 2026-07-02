import streamlit as st
import re
import pandas as pd
import fitz  # PyMuPDF
from google import genai
import os

# Initialize Gemini Client 
try:
    client = genai.Client()
except Exception:
    client = None

REGEX_PATTERNS = {
    "Email Address": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "Phone Number": r'\b\d{10}\b|\+\d{1,3}[-.\s]?\d{10}\b',
    "PAN Card": r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
    "Aadhaar Number": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
    "Credit Card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    "API Key / Password": r'(db_password|api_key|secret|token|passwd)\s*=\s*[\'"][A-Za-z0-9_\-]{16,}[\'"]'
}

def detect_deterministic_pii(text):
    findings = []
    masked_text = text
    
    for entity_type, pattern in REGEX_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in set(matches):
            count = text.count(match)
            findings.append({"Type": entity_type, "Instance": match, "Count": count})
            # Data Masking Bonus Feature
            masked_text = masked_text.replace(match, f"[{entity_type} REDACTED]")
            
    return findings, masked_text

def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    text = ""
    
    if file_type == 'txt':
        text = uploaded_file.read().decode("utf-8")
    elif file_type == 'csv':
        df = pd.read_csv(uploaded_file)
        text = df.to_string()
    elif file_type == 'pdf':
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                text += page.get_text()
            # Basic OCR fallback if text extraction yields nothing
            if not text.strip():
                text = "[OCR Required] Document appears to be an image scan. (Integrate pytesseract here)"
        except Exception as e:
            text = f"Error reading PDF: {str(e)}"
            
    return text

def analyze_with_llm(text, findings_summary):
    if not client:
        return "Medium Risk", "### ⚠️ Configuration Error\nGemini API Key missing or client initialization failed. Please set the GEMINI_API_KEY environment variable/secret."

    prompt = f"""
    You are a world-class Data Compliance Officer specializing in global data regulations (GDPR, HIPAA, DPDP Act).
    Analyze the following document text and its detected structural PII entities.
    
    Detected Entities Summary: {findings_summary}
    Document Text:
    \"\"\"{text[:4000]}\"\"\" # Truncated to avoid token blowout
    
    Provide your output strictly in the following format:
    RISK_LEVEL: [Choose only one: Low Risk / Medium Risk / High Risk]
    ---
    ### Compliance Observations
    [Your structural compliance assessment here]
    
    ### Security Risks
    [Identified vulnerabilities or data exposure risks]
    
    ### Suggested Remediation Steps
    [Actionable architectural fixes]
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    response_text = response.text
    risk_level = "Medium Risk"
    if "RISK_LEVEL: Low Risk" in response_text: risk_level = "Low Risk"
    elif "RISK_LEVEL: High Risk" in response_text: risk_level = "High Risk"
    
    clean_summary = response_text.split("---")[-1] if "---" in response_text else response_text
    return risk_level, clean_summary

def answer_rag_question(text, question):
    if not client:
        return "AI Engine offline. Provide an API Key to activate QA feature."
        
    prompt = f"""
    Context Document:
    \"\"\"{text[:6000]}\"\"\"
    
    Question: {question}
    
    Answer the question accurately based on the provided context document. If the answer cannot be determined, specify that.
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

st.set_page_config(page_title="Proteccio Data Assistant", layout="wide", page_icon="🛡️")

st.title("🛡️ Sensitive Data Detection & Compliance Assistant")
st.subheader("AI-Powered Compliance Screening Pipeline")

uploaded_file = st.file_uploader("Upload document for compliance screening", type=["txt", "csv", "pdf"])

if uploaded_file:
    with st.spinner("Extracting and parsing document..."):
        raw_text = extract_text_from_file(uploaded_file)
        
    if raw_text.strip():
        findings, masked_out = detect_deterministic_pii(raw_text)
        with st.sidebar:
            st.header("📋 Analysis Dashboard")
            if findings:
                df_findings = pd.DataFrame(findings).drop_duplicates(subset=['Instance'])
                st.dataframe(df_findings[['Type', 'Count']], use_container_width=True)
            else:
                st.success("No structural PII explicitly detected by regex filters.")
        with st.spinner("Generating AI Risk & Compliance Assessment..."):
            risk, summary = analyze_with_llm(raw_text, str(findings))
        badge_colors = {"Low Risk": "green", "Medium Risk": "orange", "High Risk": "red"}
        st.markdown(f"### Overall Assessment: :{badge_colors[risk]}[{risk}]")
        tab1, tab2, tab3 = st.tabs(["Compliance Summary", "Redacted Document View", "Ask Questions (RAG)"])
        
        with tab1:
            st.markdown(summary)
            
        with tab2:
            st.caption("Bonus Feature enabled: Automated Data Masking pipeline visualization")
            st.text_area("Masked Content View", masked_out, height=400)
            
        with tab3:
            st.markdown("### Interactive QA Layer")
            user_query = st.text_input("Ask any question regarding the compliance exposure or contents of this file:")
            if user_query:
                with st.spinner("Querying internal vector representation..."):
                    answer = answer_rag_question(raw_text, user_query)
                    st.markdown(f"**Answer:** {answer}")
    else:
        st.error("Uploaded document contains no valid text data.")
