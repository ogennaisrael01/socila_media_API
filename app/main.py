from fastapi import FastAPI, status, HTTPException
from app.routes import user_route, profile_route, following_route, post_route, likes_route, comment_route, notifications_route
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .utils.apshedular import starter, send_notif

app = FastAPI()
shedular = AsyncIOScheduler()
# Path to the favicon.ico file
favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.on_event("startup")
def startup():
    try:
        shedular.add_job(starter, "interval", seconds=10, id="starter")
        shedular.add_job(send_notif, "interval", seconds=10, id="send_notif")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={'success': False, "message": f"error sending job: {e}"})
    shedular.start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)


@app.get("/")
async def homepage():
    return {
        "status": status.HTTP_200_OK,
        "message": "Welcome to Easy connect, world"
    }

@app.on_event("shutdown")
def shutdown():
    if shedular:
        shedular.shutdown()

app.include_router(user_route.router, prefix="/api/v1")
app.include_router(profile_route.router, prefix="/api/v1")
app.include_router(following_route.router, prefix="/api/v1")
app.include_router(post_route.router, prefix="/api/v1")
app.include_router(likes_route.router, prefix="/api/v1")
app.include_router(comment_route.router, prefix="/api/v1")
app.include_router(notifications_route.router, prefix="/api/v1")