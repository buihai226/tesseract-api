from fastapi import FastAPI, File, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np

app = FastAPI()
"""Code đọc toàn bộ văn bản trong ảnh"""
# @app.get("/", response_class=PlainTextResponse)
# async def home():
#     return "OCR API is running."

# @app.post("/extract-captcha", response_class=PlainTextResponse)
# async def extract_text(file: UploadFile = File(...)):
#     try:
#         # Đọc file ảnh
#         image_bytes = await file.read()
#         image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

#         # Trích xuất toàn bộ văn bản bằng pytesseract
#         text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')

#         # Trả về kết quả
#         return text.strip() if text.strip() else "No text found in image."
#     except Exception as e:
#         return PlainTextResponse(f"Error: {str(e)}", status_code=500)


def extract_captcha_region(image: Image.Image) -> str:
    """
    Crop vùng CAPTCHA (dựa trên kích thước 1080x1920) và OCR riêng
    """
    width, height = image.size
    if width == 1080 and height == 1920:
        # Crop vùng chứa r3 
        captcha_box = (625, 1075, 775, 1145)  # (left, top, right, bottom)
        captcha_img = image.crop(captcha_box)

        # OCR captcha
        return pytesseract.image_to_string(
            captcha_img,
            lang="eng",
            config='--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ).strip()
    else:
        return "Unsupported image size for CAPTCHA crop"

@app.post("/extract-captcha")
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        full_text = pytesseract.image_to_string(image, lang="eng", config="--psm 6").strip()
        captcha_text = extract_captcha_region(image)

        return JSONResponse(content={
            "full_text": full_text,
            "captcha_text": captcha_text
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



