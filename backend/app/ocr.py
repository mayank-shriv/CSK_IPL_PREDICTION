from dataclasses import dataclass
import io
import os
import re


TEAM_ALIASES = {
    "CSK": "CSK", "CHENNAI": "CSK", "CHENNAISUPERKINGS": "CSK",
    "GT": "GT", "GUJARAT": "GT", "GUJARATTITANS": "GT",
    "RCB": "RCB", "BANGALORE": "RCB", "ROYALCHALLENGERS": "RCB",
    "MI": "MI", "MUMBAI": "MI", "MUMBAIINDIANS": "MI",
    "RR": "RR", "RAJASTHAN": "RR", "RAJASTHANROYALS": "RR",
    "KKR": "KKR", "KOLKATA": "KKR", "KOLKATANIGHTRIDERS": "KKR",
    "DC": "DC", "DELHI": "DC", "DELHICAPITALS": "DC",
    "SRH": "SRH", "HYDERABAD": "SRH", "SUNRISERSHYDERABAD": "SRH",
    "PBKS": "PBKS", "PUNJAB": "PBKS", "PUNJABKINGS": "PBKS",
    "LSG": "LSG", "LUCKNOW": "LSG", "LUCKNOWSUPERGIANTS": "LSG",
}
NUMBER_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")


@dataclass
class ExtractionResult:
    status: str
    rows: list[dict]
    confidence: float | None = None
    message: str | None = None


class ScoreboardExtractor:
    """Extract common IPL standings layouts using OpenCV and Tesseract."""

    def extract(self, content: bytes, content_type: str) -> ExtractionResult:
        if not content:
            return ExtractionResult("invalid", [], message="The uploaded file is empty.")
        if content_type == "application/pdf":
            return ExtractionResult("unsupported", [], message="PDF OCR is not configured yet. Upload a PNG, JPG, or WEBP screenshot.")

        try:
            import cv2
            import numpy as np
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            return ExtractionResult("unavailable", [], message=f"OCR dependencies are not installed: {exc.name}.")

        executable = os.getenv("TESSERACT_CMD")
        if executable:
            pytesseract.pytesseract.tesseract_cmd = executable
        try:
            image = Image.open(io.BytesIO(content)).convert("RGB")
            pixels = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            pixels = cv2.resize(pixels, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            pixels = cv2.threshold(pixels, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            data = pytesseract.image_to_data(pixels, config="--psm 6", output_type=pytesseract.Output.DICT)
        except Exception as exc:
            return ExtractionResult("failed", [], message=f"OCR could not read this image: {exc}")

        lines: dict[tuple[int, int], list[tuple[int, str]]] = {}
        confidences = []
        for index, text in enumerate(data["text"]):
            text = text.strip()
            if not text:
                continue
            key = (data["block_num"][index], data["line_num"][index])
            lines.setdefault(key, []).append((data["left"][index], text))
            try:
                confidence = float(data["conf"][index])
                if confidence >= 0:
                    confidences.append(confidence)
            except (TypeError, ValueError):
                pass

        rows = []
        for words in lines.values():
            tokens = [word for _, word in sorted(words)]
            row = self._parse_line(tokens)
            if row:
                rows.append(row)

        if not rows:
            return ExtractionResult("needs_review", [], confidence=_confidence(confidences), message="Text was detected, but no standings rows were recognized. Please enter the table manually.")
        return ExtractionResult("needs_review", rows, confidence=_confidence(confidences), message="OCR completed. Verify every extracted value before analysis.")

    @staticmethod
    def _parse_line(tokens: list[str]) -> dict | None:
        team_index = next((index for index, token in enumerate(tokens) if _team_name(token)), None)
        if team_index is None:
            return None
        numbers = [token.replace(",", "") for token in tokens[team_index + 1:] if NUMBER_PATTERN.match(token.replace(",", ""))]
        if len(numbers) < 5:
            return None
        try:
            if len(numbers) >= 6:
                played, wins, losses, no_results, points, nrr = numbers[:6]
            else:
                played, wins, losses, points, nrr = numbers[:5]
                no_results = "0"
            return {
                "team": _team_name(tokens[team_index]),
                "played": int(float(played)),
                "wins": int(float(wins)),
                "losses": int(float(losses)),
                "no_results": int(float(no_results)),
                "points": int(float(points)),
                "nrr": float(nrr),
            }
        except ValueError:
            return None


def _team_name(value: str) -> str | None:
    normalized = re.sub(r"[^A-Z]", "", value.upper())
    return TEAM_ALIASES.get(normalized)


def _confidence(values: list[float]) -> float | None:
    return round(sum(values) / len(values) / 100, 3) if values else None
