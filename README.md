# AutoScoring — Automatic Subjective Question Scoring System

FYP project for **Karakoram International University** — an NLP-powered system that automatically scores subjective exam answers using BERT-based semantic similarity.

## Features

- **Written paper support** — upload PDF or photograph handwritten/printed exam papers
- **OCR extraction** — EasyOCR reads handwriting and print from photos/PDFs
- **Teacher review** — edit OCR text before scoring if handwriting was misread
- **BERT-based scoring** via `sentence-transformers/all-MiniLM-L6-v2`
- **Detailed reports** — matched/missing concepts, keywords, strengths & weaknesses
- **Multi-factor evaluation**: semantic similarity (60%), keyword coverage (25%), coherence (15%)
- **Instructor dashboard** to manage questions, model answers, and view results
- **Typed answers** still supported alongside paper uploads
- **REST API** built with FastAPI
- **PostgreSQL** database for persistent storage
- **Docker** deployment ready

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| NLP      | BERT (MiniLM via sentence-transformers) |
| Backend  | Python, FastAPI                     |
| Frontend | React, TypeScript, Vite             |
| Database | PostgreSQL                          |
| Deploy   | Docker Compose                      |

## Quick Start (Docker)

```bash
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **API docs**: http://localhost:8000/docs
- **Demo login**: `instructor@kiu.edu.pk` / `password123`

First startup downloads the BERT model (~90MB) and seeds demo data.

## Deploy on a server

1. Push this repo to GitHub, then on the server:

```bash
git clone https://github.com/YOUR_USER/YOUR_REPO.git
cd YOUR_REPO
cp .env.example .env
# Edit .env — set PUBLIC_API_URL, PUBLIC_FRONTEND_URL, CORS_ORIGINS,
# POSTGRES_PASSWORD, and SECRET_KEY to your server IP or domain.
docker compose up --build -d
```

2. Open `http://YOUR_SERVER_IP:5173` (API on port `8000`).

3. Open firewall ports **5173** and **8000** (and **22** for SSH).

## Local Development

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL (or use docker compose up db)
export DATABASE_URL=postgresql://autoscoring:autoscoring@localhost:5432/autoscoring
python seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register instructor |
| POST | `/api/auth/login` | Login (OAuth2 form) |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET/POST | `/api/questions` | List/create questions |
| POST | `/api/questions/preview-score` | Preview score without saving |
| POST | `/api/questions/{id}/submissions` | Score a student answer |

## Scoring Methodology

1. **Semantic Similarity** — BERT embeddings compared via cosine similarity
2. **Keyword Coverage** — Overlap of key terms between model and student answer
3. **Coherence** — Heuristic based on length, sentence structure, and repetition

Final score = weighted combination scaled to the question's max score.

## Model Evaluation

Compare system scores against human teacher scores using standard grading metrics.

### CSV format

Create a file with these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `model_answer` | Yes | Reference answer |
| `student_answer` | Yes | Student response |
| `human_score` | Yes | Teacher-assigned score |
| `max_score` | No | Default: 10 |
| `title` | No | Label for the row |

A sample dataset is included at `backend/data/evaluation/sample_eval.csv`.

### Run evaluation

```bash
cd backend
python evaluate.py data/evaluation/sample_eval.csv
```

Save a JSON report for your FYP:

```bash
python evaluate.py data/evaluation/sample_eval.csv --output reports/eval_report.json
```

### Metrics reported

| Metric | What it measures |
|--------|------------------|
| **Pearson r** | Linear correlation between human and system scores |
| **Spearman ρ** | Rank-order agreement |
| **QWK (κ)** | Quadratic Weighted Kappa — standard for auto-grading |
| **MAE** | Mean Absolute Error (avg. points off) |
| **RMSE** | Root Mean Squared Error |
| **Within ±1 / ±2** | % of scores within tolerance of human score |

