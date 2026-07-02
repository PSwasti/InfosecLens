# InfosecLens
# Sensitive Data Detection & Compliance Assistant

An intelligent hybrid AI pipeline designed to ingest unstructured documents, systematically redact high-risk identifiers using local low-latency components, and utilize Large Language Models (LLM) for regulatory compliance reasoning.

## 🚀 Architecture Overview
The engine applies a **Hybrid Security Processing Framework**:
1. **Deterministic Filter Layer:** Utilizes compiled tracking expressions for immediate indexing of structured data streams (Emails, PAN Cards, Aadhaar, Credit Cards, API Keys) with zero network latency.
2. **Probabilistic Reasoning Layer:** Passes the document context window into `gemini-2.5-flash` to surface implicit compliance risks (e.g., hidden business strategies, data exposure patterns) and map hazard categories.
3. **Data Protection Layer:** Intercepts out-of-bounds metrics to return a secure, sanitized string output stream view.

---

## 🛠️ Setup Instructions

### Prerequisites
Ensure Python 3.9+ is configured locally.

### Installation
1. Clone this repository and move to the project directory:
   ```bash
   git clone <your-repo-link>
   cd <repo-name>
