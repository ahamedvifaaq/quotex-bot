from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import get_stats, get_recent_trades, init_db
from email_trade_bot import start_bot_background
import uvicorn
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    bot_task = asyncio.create_task(start_bot_background())
    yield
    # Shutdown
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats")
async def stats():
    return await get_stats()

@app.get("/api/trades")
async def trades():
    return await get_recent_trades()

if __name__ == "__main__":
    uvicorn.run("dashboard_app:app", host="127.0.0.1", port=8000, reload=True)
