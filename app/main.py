from fastapi import FastAPI, status
from app.routes import user_route, profile_route, following_route
app = FastAPI()


@app.get("/")
async def homepage():
    return {
        "status": status.HTTP_200_OK,
        "message": "Welcome to my homepage, world"
    }


app.include_router(user_route.router, prefix="/api/v1")
app.include_router(profile_route.router, prefix="/api/v1")
app.include_router(following_route.router, prefix="/api/v1")