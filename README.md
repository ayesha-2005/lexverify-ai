# LexVerify AI — Legal Research Assistant & Citation Verification System

LexVerify AI is an AI-powered legal research and document verification engine engineered specifically for Pakistani Case Law. It combines dynamic multi-agent orchestration, Retrieval-Augmented Generation (RAG) over trusted legal corpora, and a strict Citation Verification Gate to eliminate AI hallucinations and deliver verifiable legal insights.

---## 📋 Executive Summary

Legal research requires high accuracy, clear references, and zero tolerance for fabricated precedents. Standard Large Language Models (LLMs) frequently generate plausible-sounding but fictitious legal citations ("hallucinations"). **LexVerify AI** solves this critical gap by implementing a multi-agent architectural pipeline backed by FAISS vector indexes and an automated citation verifier. Every output is cross-referenced against authentic Pakistani legal databases before being presented to the user.

---## 🎯 Problem Statement1. **Hallucination Risks in Legal AI:** General-purpose LLMs generate citations to nonexistent case law, creating liability risks for legal practitioners.2. **Time-Consuming Precedent Retrieval:** Manual cross-referencing across voluminous law journals (PLD, SCMR, CLC) takes hours.3. **Lack of Verifiable Sources:** Existing AI tools rarely provide page-level or clause-level citations to verify source context.**LexVerify AI Solution:** A structured, 4-agent legal workflow with an automated **Citation Truth Gate** that verifies every cited case law precedent against verified reference files.

---## 🏗️ 4-Agent Architecture Diagram
             +---------------------------------+
             |        User Input Query         |
             +---------------------------------+
                              |
                              v
             +---------------------------------+
             |  Agent 1: Legal Research Agent  |
             |    (Query Intent & Keyword)     |
             +---------------------------------+
                              |
                              v
             +---------------------------------+
             |  Agent 2: RAG & FAISS Retriever |
             | (Vector Search over Corpus PDF) |
             +---------------------------------+
                              |
                              v
             +---------------------------------+
             |  Agent 3: Citation Truth Gate   |
             | (Verification & Anti-Halluc)    |
             +---------------------------------+
                              |
                              v
             +---------------------------------+
             |  Agent 4: Synthesis & UI Agent  |
             |  (Structured Legal Summary/UI)  |
             +---------------------------------+
                              |
                              v
             +---------------------------------+
             |     Streamlit Web Interface     |
             +---------------------------------+

---

## 🛠️ Tech Stack

- **Frontend & UI:** Streamlit
- **AI & Orchestration:** Python, LangChain, Groq API
- **Vector Database & RAG:** FAISS (`faiss-cpu`), Sentence-Transformers
- **Environment & Config Management:** `python-dotenv`, `pydantic`
- **Version Control:** Git, GitHub

---

## ⚡ Quickstart Setup Instructions

### 1. Repository Clone
```bash
git clone [https://github.com/ayesha-2005/lexverify-ai.git](https://github.com/ayesha-2005/lexverify-ai.git)
cd lexverify-ai
2. Virtual Environment Setup
Bash

python -m venv venv
venv\Scripts\activate   # On Windows
3. Dependencies Install
Bash

pip install -r requirements.txt
4. Environment Keys Setup
Create a .env file in the root directory:

Code snippet

GROQ_API_KEY=your_groq_api_key_here
5. Run Application Local
Bash

streamlit run app.py
🧪 Demo Scenarios
Authentic Precedent Query: Querying Pakistani criminal procedure grounds for bail to fetch verified statutory sections.
Citation Verification Gate: Identifying and flagging fake case law references automatically.
Legal Document Analysis: Extracting key legal clauses and analyzing risk factors.
🛡️ Legal Disclaimer
Disclaimer: LexVerify AI is an legal research assistant for Pakistani Case Law. Results are generated for analytical purposes and do not constitute formal legal advice.
👥 Team Roles
Member 1 (AI Lead): Agent prompts and multi-agent workflow architecture.
Member 2 (RAG Lead): PDF legal corpus indexing, FAISS vector store, and retriever logic.
Member 3 (UI Lead): Streamlit frontend design, layout components, and response formatting.
Member 4 (Integration Lead): Repository setup, environment dependencies, security governance, disclaimers, and integration testing.