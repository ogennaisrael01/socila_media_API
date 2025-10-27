from fastapi import FastAPI, status
from app.routes import user_route, profile_route, following_route, post_route, likes_route, comment_route
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Path to the favicon.ico file
favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


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


app.include_router(user_route.router, prefix="/api/v1")
app.include_router(profile_route.router, prefix="/api/v1")
app.include_router(following_route.router, prefix="/api/v1")
app.include_router(post_route.router, prefix="/api/v1")
app.include_router(likes_route.router, prefix="/api/v1")
app.include_router(comment_route.router, prefix="/api/v1")