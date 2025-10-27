import cloudinary
import cloudinary.uploader
from cloudinary import exceptions
from ..config.settings import settings
import logging
from fastapi import status, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


def upload_image(image_url: str):
    if not image_url.endswith(".jpg") or image_url.endswith(".png"):
        logging.error("Invalid image format, only '.jpg' or '.png' is allowed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": "Invalid image format' Only .jpg or .png is allowed"})
    
    try:
        uploader = cloudinary.uploader.upload(image_url)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": f"error {e}"})
    return uploader