from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import PlainTextResponse
import pytesseract
from PIL import Image
import io
import logging
import os

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.route("/", methods=["GET", "HEAD"])
async def health_check(request: Request):
    logger.info(f"Health check endpoint accessed with method: {request.method}")
    return PlainTextResponse("Application is running")

@app.get("/extract-captcha", response_class=PlainTextResponse)
async def extract_captcha_get():
    logger.info("GET request to /extract-captcha")
    return "This endpoint requires a POST request with a file. Use multipart/form-data with key 'file'."

@app.post("/extract-captcha", response_class=PlainTextResponse, responses={200: {"content": {"text/plain": {}}}})
async def extract_captcha(file: UploadFile = File(...)):
    try:
        logger.info("Reading and processing image")
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        logger.info("Running OCR on image with Tesseract")
        # Sử dụng Tesseract để trích xuất văn bản
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')

        if text.strip():
            logger.info(f"Captcha found: {text.strip()}")
            return text.strip()
        else:
            logger.info("No captcha found")
            return "Can't found"
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Environment variable PORT: {os.environ.get('PORT')}")
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
