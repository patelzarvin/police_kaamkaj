# Gujarat Police Sentinel — Installation & Setup Guide

---

## Prerequisites

- **Python**: 3.11 or 3.12
- **Node.js**: v18+ and `npm`
- **Docker & Docker Compose** (Optional for containerized deployment)
- **PostgreSQL 16 + PostGIS extension** (Optional for local PostgreSQL deployment; SQLite dev fallback included)

---

## Step-by-Step Local Environment Setup

### 1. Clone & Environment Configuration
Copy environment parameters:
```bash
cp .env.example .env
```

### 2. Python Virtual Environment Setup
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Initialize Database & Seed Catalogue Data
```bash
python database/seeds/seed_data.py
```

### 4. Launch FastAPI Backend Server
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation available at `http://localhost:8000/docs`.

### 5. Launch React Frontend Command Center UI
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend available at `http://localhost:3000`.

---

## Running Integration & Unit Tests
```bash
python -m pytest tests/test_anpr_normalizer.py tests/test_journey.py
```
