# AI Data Extractor

A full-stack dataset extraction application. Upload PDFs, images, Word documents, spreadsheets, and plain-text files; OCR and parse them; define a structured schema; extract data with an AI agent; review it in an interactive table; and export to **JSON, JSONL, CSV, TSV, or Excel**.

---

## Features

| Feature | Details |
|---|---|
| **File upload** | Drag-and-drop or click-to-select. Supports PDF, PNG, JPG, TIFF, BMP, WebP, DOCX, XLSX, XLS, CSV, TSV, TXT, MD. Up to 50 MB per file. |
| **OCR** | Tesseract OCR via `pytesseract` for images and scanned PDFs. `pdfplumber` for PDFs with a text layer. |
| **Parsing** | `pdfplumber` (PDF), `python-docx` (Word), `pandas`/`openpyxl` (Excel), standard `csv` module, `chardet` for encoding detection. |
| **Schema editor** | Define named fields with types (`string`, `number`, `boolean`, `date`, `list`), optional descriptions, and required flags. |
| **AI extraction** | GPT-4o reads the raw text of every uploaded file and returns structured records matching your schema. |
| **Interactive table** | Sort, filter, paginate, double-click to edit cells, delete rows. All edits sync back to the server. |
| **AI agent** | Conversational assistant (GPT-4o with function calling) that can suggest schemas, run extraction, and answer questions about your data. |
| **Export** | One-click download as JSON, JSONL, CSV, TSV, or XLSX. |

---

## Project Structure

```
├── backend/            # Python FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── state.py        # In-memory job store
│   ├── models/         # Pydantic schemas
│   ├── routers/        # FastAPI route handlers
│   └── services/       # OCR, parsing, export, AI logic
│
├── frontend/           # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/ # FileUpload, DataTable, SchemaEditor, AiAgent, ExportPanel
│   │   ├── services/   # axios API client
│   │   ├── store/      # Zustand global state
│   │   └── types/      # Shared TypeScript types
│   ├── Dockerfile
│   └── nginx.conf
│
└── docker-compose.yml
```

---

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (easiest), or
- **Python 3.11+** and **Node 20+** installed locally
- An **OpenAI API key** (GPT-4o access recommended)
- Tesseract OCR installed locally if running outside Docker (`brew install tesseract` / `apt install tesseract-ocr`)

### Option A – Docker Compose (recommended)

```bash
# 1. Copy env file and add your OpenAI key
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY=sk-...

# 2. Start everything
docker compose up --build
```

Open **http://localhost:5173** in your browser.

### Option B – Run locally

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # edit .env with your OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Usage Workflow

1. **Upload** — drag files onto the Upload tab (PDFs, images, Word docs, spreadsheets, etc.)
2. **Schema** — define the fields you want to extract (or ask the AI Agent to suggest one)
3. **Extract** — click **Run Extraction**; GPT-4o reads every document and fills the table
4. **Review** — open the **Data Table** tab, search/sort/edit cells as needed
5. **Export** — go to **Export** and download in your preferred format

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI secret key |
| `OPENAI_MODEL` | `gpt-4o` | Model used for extraction and the agent |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed CORS origins |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload size per file |

---

## Tech Stack

**Backend:** Python · FastAPI · pdfplumber · pytesseract · python-docx · pandas · openpyxl · OpenAI SDK

**Frontend:** React 19 · TypeScript · Vite · TailwindCSS · TanStack Table · Zustand · axios · react-dropzone · lucide-react
