# ⚖️ LexVerify AI

### Legal Research Assistant \& Citation Verification System for Pakistani Case Law

> \*\*Research. Retrieve. Verify. Respond.\*\*

[!\[Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=white)](https://www.python.org/)
[!\[Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit\&logoColor=white)](https://streamlit.io/)
[!\[Groq](https://img.shields.io/badge/Groq-API-orange)](https://groq.com/)
[!\[FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-green)](https://github.com/facebookresearch/faiss)
[!\[License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

\---

## 📑 Table of Contents

* [Overview](#-overview)
* [Key Features](#-key-features)
* [System Architecture](#-system-architecture)
* [Multi-Agent Pipeline](#-multi-agent-pipeline)
* [Tech Stack](#-tech-stack)
* [Project Structure](#-project-structure)
* [Quick Start](#-quick-start)
* [Team Roles](#-team-roles)
* [Legal Disclaimer](#-legal-disclaimer)
* [License](#-license)

\---

## 🔎 Overview

**LexVerify AI** is an Agentic AI-powered legal research assistant designed to help users research Pakistani case law while reducing the risk of fabricated or unsupported legal citations.

The system combines **Retrieval-Augmented Generation (RAG)**, **FAISS vector search**, a **four-agent workflow**, and a **Deterministic Citation Truth Gate**.

Instead of allowing the language model to independently decide whether a legal citation is genuine, LexVerify checks candidate citations against a trusted citation registry before allowing them to appear as verified sources.

### Core Principle

> \*\*The LLM generates research insights. The Truth Gate determines citation validity.\*\*

\---

## ✨ Key Features

### 🛡️ Zero-Hallucination-Oriented Research

LexVerify is designed to minimize unsupported legal claims by grounding responses in retrieved documents and verified citation records.

> No AI system can guarantee literal zero hallucinations. LexVerify therefore uses verification and evidence constraints to \*\*reduce and detect unsupported citations\*\*.

### 🚦 Deterministic Citation Truth Gate

A dedicated verification layer checks extracted citations against a structured citation registry.

```text
Candidate Citation
       │
       ▼
Normalize Citation
       │
       ▼
Search Citation Registry
       │
   ┌───┴────┐
   │        │
 MATCH    NO MATCH
   │        │
   ▼        ▼
VERIFIED  UNVERIFIED
```

### 🔍 FAISS Semantic Search

Relevant legal passages are retrieved using vector similarity search powered by **FAISS** and **Sentence-Transformers**.

### 🏷️ Audit \& Verification Badges

The interface clearly distinguishes verified and unverified citations so users can understand the research trail behind an answer.

### 🤖 Four-Agent Workflow

LexVerify separates the research process into four specialized stages:

* Research
* Retrieval
* Verification
* Synthesis

### 📚 Evidence-Grounded Answers

The Synthesis Agent receives retrieved and verified evidence rather than relying solely on the model's internal knowledge.

\---

## 🏗️ System Architecture

```text
                    ┌───────────────────────┐
                    │       USER QUERY      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   RESEARCH AGENT      │
                    │ Query Understanding   │
                    │ Search Decomposition  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   RETRIEVAL AGENT     │
                    │  Sentence Embeddings  │
                    │    FAISS Top-K Search  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ VERIFICATION AGENT    │
                    │ Citation Truth Gate   │
                    │ Deterministic Check   │
                    └───────────┬───────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
                   VERIFIED          UNVERIFIED
                       │                 │
                       ▼                 ▼
              ┌────────────────┐   ┌───────────────┐
              │ SYNTHESIS      │   │ FLAG / REJECT │
              │ AGENT          │   │ Citation      │
              └───────┬────────┘   └───────────────┘
                      │
                      ▼
            ┌──────────────────────┐
            │ GROUNDED FINAL       │
            │ LEGAL RESEARCH       │
            │ RESPONSE             │
            └──────────────────────┘
```

\---

## 🤖 Multi-Agent Pipeline

|Agent|Responsibility|Main Output|
|-|-|-|
|**Agent 1 — Research**|Understands the user's legal question, identifies important concepts, and decomposes the query into useful search directions.|Structured research intent and search terms|
|**Agent 2 — Retrieval**|Converts search queries into embeddings and searches the FAISS vector index for relevant legal passages.|Relevant documents, chunks, and evidence|
|**Agent 3 — Verification**|Extracts and normalizes citations and checks them against the trusted citation registry using deterministic matching.|`VERIFIED` / `UNVERIFIED` citation status|
|**Agent 4 — Synthesis**|Produces the final response using retrieved evidence and verified citations while avoiding unsupported citations.|Grounded legal research response|

### 🔐 Verification Rule

```text
If citation exists in trusted registry
        → VERIFIED
        → Eligible for final response

If citation does not exist
        → UNVERIFIED
        → Flagged / excluded from verified evidence
```

\---

## 🧰 Tech Stack

### Artificial Intelligence

* **Groq API**
* **Model:** `openai/gpt-oss-120b`
* Agent-based workflow
* Retrieval-Augmented Generation (RAG)

### Vector Search \& Embeddings

* **FAISS**
* **Sentence-Transformers**
* **Embedding Model:** `all-MiniLM-L6-v2`

### Backend

* **Python**
* **Pydantic**
* JSON / structured citation registry

### Frontend

* **Streamlit**

### Development \& Deployment

* Git / GitHub
* Environment variables for API secrets
* Streamlit-compatible deployment

\---

## 📁 Project Structure

```text
lexverify-ai/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .env
│
├── data/
│   ├── documents/
│   │   └── \*.pdf
│   │
│   ├── metadata.json
│   └── citations.json
│
├── src/
│   │
│   ├── agents/
│   │   ├── research\_agent.py
│   │   ├── retrieval\_agent.py
│   │   ├── verification\_agent.py
│   │   └── synthesis\_agent.py
│   │
│   ├── rag/
│   │   ├── ingest.py
│   │   ├── embeddings.py
│   │   └── retriever.py
│   │
│   └── utils/
│       └── helpers.py
│
└── .gitignore
```

> \*\*Important:\*\* Never commit `.env` or expose API keys in the repository.

\---

## 🚀 Quick Start

### 1\. Clone the Repository

```bash
git clone https://github.com/YOUR\_USERNAME/lexverify-ai.git
cd lexverify-ai
```

### 2\. Create a Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3\. Install Requirements

```bash
pip install -r requirements.txt
```

### 4\. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ\_API\_KEY=your\_groq\_api\_key\_here
```

Do **not** upload this file to GitHub.

Make sure `.gitignore` contains:

```text
.env
.venv/
\_\_pycache\_\_/
\*.pyc
```

### 5\. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at the local Streamlit address shown in the terminal.

\---

## 👥 Team Roles

### 👤 Member 1 — AI / Agent Lead

* Agent architecture
* Agent prompts
* Agent orchestration
* Groq API integration
* Research and Synthesis logic

### 👤 Member 2 — RAG / Data Lead

* Pakistani legal corpus
* Document processing
* Text extraction
* Chunking
* Sentence-Transformers embeddings
* FAISS index
* Citation registry

### 👤 Member 3 — Streamlit / UI Lead

* Streamlit interface
* Query input
* Agent workflow visualization
* Verification badges
* Evidence display
* Final response interface

### 👤 Member 4 — Integration / Deployment Lead

* Component integration
* Testing
* GitHub repository
* Deployment
* README
* Presentation slides
* Demo video
* Final submission

\---

## ⚖️ Legal Disclaimer

**LexVerify AI is a legal research assistance prototype and is not a substitute for professional legal advice, legal representation, or independent verification of legal authorities.**

The system operates on a curated legal corpus and may not contain every relevant Pakistani judgment, statute, amendment, or legal authority.

Users should verify important legal information against the **original and authoritative legal sources** before relying on it for professional, academic, or legal decisions.

The citation verification mechanism is designed to reduce unsupported or fabricated citations; it does not constitute a guarantee of legal accuracy.



\---

<p align="center">
  <strong>LexVerify AI</strong><br>
  Research. Retrieve. Verify. Respond.
</p>

