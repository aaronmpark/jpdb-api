from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from typing import Optional
import anki
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aaronmpark.github.io"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/create_deck")
def create_deck(
    url: Optional[str] = Query(
        default="",
        description="JPDB vocabulary list URL"),
    filename: Optional[str] = Query(
        default="",
        description="Output Anki deck filename")
):
    vocab, deck_name = anki.scrape_vocab(url)
    anki.create_anki_deck(vocab, filename, deck_name)
    if not os.path.exists(filename):
        return {"error": "File not found"}
    return FileResponse(
        path=filename,
        media_type='application/octet-stream',
        filename=filename
    )