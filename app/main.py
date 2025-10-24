from fastapi import FastAPI, status
from app.routes import user_route, profile_route, following_route, post_route
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

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
        "message": "Welcome to my homepage, world"
    }


app.include_router(user_route.router, prefix="/api/v1")
app.include_router(profile_route.router, prefix="/api/v1")
app.include_router(following_route.router, prefix="/api/v1")
app.include_router(post_route.router, prefix="/api/v1")