# /README.md

# AI-Powered CV and Project Evaluator

This project is a backend service designed to automate the initial screening of job applications. It uses a Retrieval-Augmented Generation (RAG) pipeline with a Large Language Model (LLM) to evaluate a candidate's CV and project report against a job description and scoring rubrics.

## Tech Stack

- **Backend Framework**: FastAPI
- **Asynchronous Tasks**: Celery with Redis
- **Vector Database**: ChromaDB (Persistent Local Storage)
- **LLM Provider**: OpenAI (GPT-4o)
- **PDF Parsing**: PyPDF
- **Embeddings**: Sentence-Transformers

## Project Structure

```
/
|-- app/              # Core application source code
|-- scripts/          # Helper scripts (e.g., data ingestion)
|-- ground_truth_docs/# Source documents for RAG
|-- uploads/          # Storage for uploaded files
|-- chroma_db_storage/# Persistent storage for ChromaDB
|-- requirements.txt  # Python dependencies
|-- README.md         # This file
```

## Setup and Running the Project

### 1. Prerequisites

- Python 3.9+
- Redis Server (must be running locally)
- An OpenAI API Key

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd ai-cv-evaluator
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    Create a file named `.env` in the root directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY="sk-..."
    ```

### 3. Data Ingestion

Before running the application, you need to populate the vector database with the ground truth documents.

```bash
python scripts/ingest_data.py
```
This will create a `chroma_db_storage` directory containing the vector embeddings.

### 4. Running the Services

You need to run three separate processes in three different terminal windows.

**Terminal 1: Start Redis (if not already running as a service)**
```bash
redis-server
```

**Terminal 2: Start the Celery Worker**
Make sure you are in the project's root directory.
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

**Terminal 3: Start the FastAPI Server**
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. You can access the auto-generated documentation at `http://127.0.0.1:8000/docs`.

## API Usage Flow

1.  **`POST /upload`**: Upload the candidate's CV and project report. You will receive unique IDs for each document.
2.  **`POST /evaluate`**: Use the document IDs from the previous step to start the evaluation process. You will receive a `job_id`.
3.  **`GET /result/{job_id}`**: Poll this endpoint periodically using the `job_id` to check the status. Once `status` is "completed", the `result` field will contain the full evaluation.