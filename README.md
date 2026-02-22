# AI Code Builder

An enterprise-grade AI-powered tool that transforms natural language data instructions into executable Python code.

## Features

- **Upload** CSV or XLSX files
- **Write** step-by-step instructions in plain English
- **Refine** instructions into a structured AI prompt (Claude-powered, streaming)
- **Generate** Python transformation code (streaming into Monaco editor)
- **Edit** the generated code directly in the browser
- **Execute** code in a sandboxed environment using your uploaded data
- **Preview** output rows in-browser, then **download** the full CSV

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| UI | Tailwind CSS + Shadcn/UI |
| Code Editor | Monaco Editor |
| State | Zustand + TanStack Query |
| Backend | FastAPI (Python 3.12) |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| Data | pandas + openpyxl + pyarrow |
| Sandbox | RestrictedPython + subprocess isolation |

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- An Anthropic API key

### Local Development

**Backend:**
```bash
cd backend
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
pip install poetry
poetry install
poetry run uvicorn app.main:app --reload
```
Backend runs at http://localhost:8000. API docs at http://localhost:8000/docs.

**Frontend:**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Frontend runs at http://localhost:5173.

### Docker (Production)

```bash
cp backend/.env.example backend/.env
# Set ANTHROPIC_API_KEY in backend/.env

docker-compose up --build
```

App available at http://localhost:80.

### Docker (Development — hot reload)

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Configuration

All settings are environment-variable driven. See:
- [`backend/.env.example`](backend/.env.example) — backend config
- [`frontend/.env.example`](frontend/.env.example) — frontend config

Key settings:
| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Your Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model for code generation |
| `SANDBOX_TIMEOUT_SECONDS` | `30` | Max execution time |
| `MAX_UPLOAD_SIZE_MB` | `50` | File size limit |
| `PREVIEW_ROW_COUNT` | `50` | Preview rows shown |

## Security

The code execution sandbox uses 4 isolation layers:
1. **AST validation** — blocks dangerous imports and builtins before execution
2. **Subprocess isolation** — code runs in a child process with a minimal environment
3. **Import allowlist** — only pandas, numpy, os, pathlib, re, datetime, math, json, csv, collections
4. **Process timeout** — hard kill after `SANDBOX_TIMEOUT_SECONDS`

## Project Structure

```
ai-code-builder/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # Endpoints: upload, instructions, codegen, execution
│   │   ├── config/         # Pydantic settings
│   │   ├── prompts/        # AI prompt templates
│   │   ├── sandbox/        # Code execution sandbox
│   │   ├── services/       # Business logic
│   │   ├── session/        # In-memory session store
│   │   └── schemas/        # Pydantic request/response models
│   └── tests/
├── frontend/                # React + TypeScript frontend
│   └── src/
│       ├── components/     # UI components
│       ├── hooks/          # Custom React hooks
│       ├── store/          # Zustand stores
│       ├── services/       # API client
│       └── utils/          # SSE parser, formatters, validation
├── docker-compose.yml
└── .github/workflows/ci.yml
```
