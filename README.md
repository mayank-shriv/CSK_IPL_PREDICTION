# IPL Qualification Analyzer

A deterministic IPL playoff qualification calculator with an OCR-ready upload flow.

## Run the backend

```powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload
```

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

The qualification engine is independent of the UI and accepts verified standings, fixtures, and season rules. OCR is deliberately isolated behind `POST /api/scoreboard/extract`; connect a provider there without changing the rules engine.

Season rules are explicit in `backend/app/rules.py`. The included 2026 config is marked draft until verified against an official IPL/BCCI source.

## Deploy on Render

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Render will read `render.yaml` and create the API and frontend services.
4. Wait for the API deployment, then confirm its URL in the frontend service environment as `VITE_API_URL`.
5. Redeploy the frontend after changing that variable. The API health check is `/api/health`.

The frontend uses `VITE_API_URL`; locally it defaults to `http://127.0.0.1:8000`. The current OCR class is a provider boundary and does not perform OCR yet. Render does not include the Tesseract executable by default, so use a hosted OCR provider or add a Docker-based OCR service before expecting extracted rows.

## OCR setup

The backend now uses Tesseract with OpenCV preprocessing. On Windows, install the native Tesseract program separately, then install the Python dependencies:

```powershell
cd backend
py -m pip install -r requirements.txt
```

If Tesseract is not on `PATH`, set its executable path before starting FastAPI:

```powershell
$env:TESSERACT_CMD = 'C:\Program Files\Tesseract-OCR\tesseract.exe'
py -m uvicorn app.main:app --reload
```

Render uses `backend/Dockerfile`, which installs `tesseract-ocr` automatically. After pushing these changes, trigger a new Render deploy. OCR supports PNG, JPG, and WEBP screenshots; PDF extraction is intentionally rejected until a PDF-to-image step is added.
