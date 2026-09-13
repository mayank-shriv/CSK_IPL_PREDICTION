from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .models import Fixture, SeasonRules, Standing
from .ocr import ScoreboardExtractor
from .qualification import analyze
from .rules import SEASON_RULES, get_season_rules
from .serializers import result_to_dict

app = FastAPI(title="IPL Qualification Analyzer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https://[a-z0-9-]+\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
extractor = ScoreboardExtractor()


class AnalyzeRequest(BaseModel):
    season: int
    selected_team: str
    standings: list[dict[str, Any]] = Field(min_length=2)
    remaining_matches: list[dict[str, Any]] = []


@app.get("/")
def root():
    return {"service": "IPL Qualification Analyzer", "health": "/api/health", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/seasons")
def seasons():
    return [{"season": season, "rules_version": rules.rules_version} for season, rules in SEASON_RULES.items()]


@app.get("/api/seasons/{season}/rules")
def rules(season: int):
    try:
        return result_to_dict(get_season_rules(season))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/seasons/{season}/fixtures")
def fixtures(season: int):
    if season not in SEASON_RULES:
        raise HTTPException(status_code=404, detail="Season is not configured.")
    return {"season": season, "fixtures": [], "source": "manual entry required"}


@app.post("/api/scoreboard/extract")
async def extract_scoreboard(file: UploadFile = File(...)):
    allowed = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Upload PNG, JPG, WEBP, or PDF.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Files must be smaller than 10 MB.")
    extraction = extractor.extract(content, file.content_type)
    return {"status": extraction.status, "message": extraction.message, "confidence": extraction.confidence, "rows": extraction.rows}


@app.post("/api/qualification/analyze")
def qualification(request: AnalyzeRequest):
    try:
        rules_config = get_season_rules(request.season)
        result = analyze(
            [Standing(**row) for row in request.standings],
            [Fixture(**match) for match in request.remaining_matches],
            request.selected_team,
            rules_config,
        )
        return result_to_dict(result)
    except (TypeError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
