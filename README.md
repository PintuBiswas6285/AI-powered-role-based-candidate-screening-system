# AI-Powered Role-Based Candidate Screening System

This project implements the PGAGI AI/ML & Backend Intern assignment: a role-based technical interview simulator powered by a modular RAG pipeline.

## Tech Stack

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database: SQLite through SQLAlchemy
- RAG: role-specific `.txt`/`.pdf` knowledge base, chunking, deterministic local embeddings, cosine retrieval, traceable generated questions
- Resume input: `.txt` and text-based `.pdf` resumes

## Features

- Candidate resume upload and target role selection
- Resume parsing with skill, technology, domain, keyword, and seniority extraction
- Role-specific knowledge ingestion from `backend/data/knowledge_base`
- Chunking, embedding generation, and persisted vector store
- Dynamic question generation influenced by resume signals and retrieved context
- Interactive interview flow with stored questions and answers
- Basic answer scoring, feedback, and final session summary
- Traceability from each question to retrieved context chunks

## Project Structure

```text
backend/
  app/
    api/              FastAPI routes
    core/             config and database setup
    models/           SQLAlchemy models
    schemas/          Pydantic response/request contracts
    services/         resume parsing, RAG, question generation, scoring
  data/
    knowledge_base/   role-specific corpus files
frontend/
  src/
    api/              backend client
    styles/           application CSS
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. API docs are available at `http://localhost:8000/docs`.

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

The UI runs at `http://localhost:5173`.

## How The RAG Pipeline Works

1. Knowledge files are loaded from role folders such as `AI_ML_Engineer` and `Backend_Engineer`.
2. Documents are split into overlapping chunks to preserve local context.
3. Each chunk is embedded with a deterministic hashing embedder and stored in `backend/data/vector_store.json`.
4. When a session starts, the resume is parsed and converted into structured profile signals.
5. The selected role and resume signals are used to build a retrieval query.
6. The highest-scoring chunks are attached to the generated question.
7. Every question, answer, retrieved context, rationale, score, and feedback item is persisted.

## Using The Assignment Books

The seeded `.txt` corpus lets the system run immediately. To align the RAG layer with the assignment's primary-source expectation, download the provided books and place the PDFs in the relevant folder under `backend/data/knowledge_base`. The backend supports text-based PDFs through `pypdf`.

After adding or replacing knowledge files, delete `backend/data/vector_store.json` and restart the backend. It will rebuild embeddings from the updated corpus.

## Design Decisions

- The local hashing embedder keeps the assignment runnable without paid API keys.
- The vector store is persisted as JSON for simplicity, while SQLAlchemy stores interview session records.
- Service modules are separated so real embedding models, LLMs, PostgreSQL, or a dedicated vector database can be swapped in later.
- Generated questions are not static templates only: they adapt to role, resume signals, previous topics, retrieved chunks, and previous answer score.

## Demo Video Checklist

Show these steps in the mandatory video:

1. Start backend and frontend.
2. Upload a resume and select a role.
3. Show extracted resume signals.
4. Answer at least two generated questions.
5. Show retrieved context attached to a question.
6. Finish the interview and show the final summary report.
