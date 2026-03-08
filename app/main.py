from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app.routes import events, reviews

app = FastAPI(title="Evently", description="Event aggregation from Dice, Songkick, Timeout & Chortle")

app.include_router(events.router)
app.include_router(reviews.router)

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir)) if templates_dir.exists() else None


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("<p>Evently API. Use <a href='/docs'>/docs</a> for the API.</p>")


@app.get("/map", response_class=HTMLResponse)
def map_page(request: Request):
    if templates:
        return templates.TemplateResponse("map.html", {"request": request})
    return HTMLResponse("<p>Map view: add templates/map.html</p>")


@app.get("/health")
def health():
    return {"status": "ok"}
