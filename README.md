# Take-Home Challenge: RFP Answer Generation Tool

## Overview

A 3 to 5-hour AI-assisted development challenge for senior/staff backend/fullstack engineers that evaluates how candidates use AI tools, their architectural thinking, documentation quality, and ability to explain their decisions.

## Candidate Instructions

### RFP Answer Generator Challenge

**Time Limit:** 3-5 hours (honor system - we trust you)

**Required Tools:** AI-assisted development (Cursor, Claude Code, Copilot, etc.)

### Setup and Submission

1. Fork this repo
2. Do the work (see Challenge Specification below)
3. Add @noahpeden, @emirbirlik-dev, @Muhammad-Talha-Hashmi, and @mrkhalil6 to it
4. Email noah@heyiris.ai, khalil@heyiris.ai, emir@heyiris.ai, talha@heyiris.ai and gadi@heyiris.ai when you've finished with the github repo link

### About This Boilerplate

This repo includes a fully wired Django + Next.js boilerplate (Docker, DRF, Tailwind, CORS, sample data, etc.) so you can skip the scaffolding and spend your time on the interesting work: RAG implementation, API design, data modeling, and frontend UX.

**You are not required to use it.** If you'd rather start from scratch or use a different stack entirely, go for it. The boilerplate is here to save you time, not to constrain you.

### API Key

Noah will provide you with an Anthropic API key to use for this challenge. Add it to your `.env` file:

```
ANTHROPIC_API_KEY=<key-from-noah>
```

---

## Getting Started

### Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env

# 2. Build, start, migrate, and seed — one command
make setup

# 3. Open in your browser
#    Backend API:  http://localhost:8000/api/
#    Frontend:     http://localhost:3000
#    Django Admin: http://localhost:8000/admin/
```

### Make Commands

| Command | Description |
|---|---|
| `make setup` | Build containers, run migrations, seed sample data |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make migrate` | Run Django migrations |
| `make seed` | Load sample documents and RFP |
| `make shell` | Open Django shell |
| `make test` | Run backend tests |
| `make logs` | Tail all service logs |
| `make superuser` | Create Django admin superuser |

### Running Without Docker

If you prefer to run locally without Docker:

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate        # Uses SQLite when POSTGRES_DB is not set
python manage.py load_sample_data
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run dev
```

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Next.js    │────▶│  Django DRF  │────▶│  PostgreSQL  │
│   :3000      │     │  :8000       │     │  (pgvector)  │
└─────────────┘     └──────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    Redis     │  (optional, for Celery)
                    └──────────────┘
```

**What's provided:**
- Docker Compose with Postgres (pgvector), Redis, Django, and Next.js
- Django project with DRF, CORS, and basic Document/RFPDocument models
- Next.js app with Tailwind CSS, routing, nav, API client, and reusable components
- Sample data: 3 company documents + 1 RFP with 5 questions
- Seed command: `python manage.py load_sample_data`

**What you build:**
- RAG pipeline (document processing, embeddings, retrieval, generation)
- Additional models (Questions, Answers, chunks, etc.)
- API endpoints for question extraction and answer generation
- Frontend page implementations (documents, RFP, answers)

---

## Where to Start

The boilerplate is set up so you can jump straight into the interesting work. Here's where to look:

### Backend
- **`backend/documents/models.py`** — `Document` and `RFPDocument` are done. Commented-out `Question` and `Answer` skeletons are there for inspiration — change them however you want.
- **`backend/documents/views.py`** — Empty `ModelViewSet`s with TODO comments. Add your upload handling, question extraction, and answer generation logic.
- **`backend/documents/serializers.py`** — Basic serializers provided. Add more as your API grows.
- **`backend/documents/urls.py`** — DRF router ready. Register new viewsets as you create them.
- **`backend/requirements.txt`** — Commented-out dependencies for OpenAI, LangChain, ChromaDB, pgvector, Celery, etc. Uncomment what you need.

### Frontend
- **`frontend/src/app/documents/page.tsx`** — Build the document management UI
- **`frontend/src/app/rfp/page.tsx`** — Build the RFP upload and question extraction UI
- **`frontend/src/app/answers/page.tsx`** — Build the answer review UI
- **`frontend/src/lib/api.ts`** — API client with Document and RFP methods. Add your own.
- **`frontend/src/lib/types.ts`** — TypeScript interfaces. Add Question, Answer, etc.
- **`frontend/src/components/ui/FileUpload.tsx`** — Ready-to-use drag-and-drop file upload component

---

## Challenge Specification

### The Problem

Build a simplified RFP (Request for Proposal) Answer Generator - a tool that takes questions from an RFP document and generates answers using a knowledge base of company documents.

**Time Limit:** 3-5 Hours

**IMPORTANT** Candidates MUST use AI agentic development tools (preferably Codex or Claude Code, but Cursor, GitHub Copilot, are alloowed) and document their AI collaboration throughout. This is very important as you will not get through the project unless you use AI to its fullest extent. At Iris we use agentic development for everything and shipping with speed and quality are our biggest priorities and the best way to do that is with agentic, compound engineering. 

## Requirements

### Core Functionality (Must Complete)

- Document Ingestion API
- Question Answering API
- Basic RAG Implementation
- Delightful Frontend allowing a user to upload documents, an RFP, and a place to review answers to the RFP from the system you build.

### Documentation Requirements (Critical)

- Purpose
- System design decisions and why
- How AI tools were used, what worked/didn't
- What you'd do differently with more time
- API documentation (or OpenAPI spec)

### Stretch Goals (If Time Permits)

- Async processing with Celery/Redis
- Vector embeddings for semantic search
- Batch question processing
- Answer caching
- Confidence scoring logic
- Frontend/Backend Testing

## Tips
- Our stack is Django Rest Framework on the backend and Next.js on the Frontend, but if you're more comfortable in a different stack feel free to use it!
- Prioritize working core features over stretch goals
- Document as you go, not at the end
- It's okay to not finish everything
- We care more about your thinking than your typing
