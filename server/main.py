from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import json
import asyncio

from .database import init_db
from .scheduler import load_jobs_into_scheduler, scheduler
from .api import router as api_router
from .executor import run_websockets, get_active_log_buffer

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    load_jobs_into_scheduler()
    yield
    scheduler.shutdown()

app = FastAPI(title="CronFrog", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.websocket("/api/ws/runs/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: int):
    await websocket.accept()
    if run_id not in run_websockets:
        run_websockets[run_id] = []
    run_websockets[run_id].append(websocket)
    
    buffer = get_active_log_buffer(run_id)
    if buffer:
        for log in buffer:
            try:
                await websocket.send_text(json.dumps(log))
            except:
                pass
            
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if run_id in run_websockets:
            if websocket in run_websockets[run_id]:
                run_websockets[run_id].remove(websocket)
            if not run_websockets[run_id]:
                del run_websockets[run_id]
    except Exception:
        pass

base_dir = os.path.dirname(os.path.dirname(__file__))

public_dir = os.path.join(base_dir, 'public')
os.makedirs(public_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8585))
    uvicorn.run(app, host="0.0.0.0", port=port)
