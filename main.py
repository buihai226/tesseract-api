from fastapi import FastAPI, File, UploadFile
from fastapi.responses import PlainTextResponse
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


def extract_captcha_from_text(full_text: str) -> str:
    """
    Hàm lọc captcha từ đoạn văn bản bằng cách tìm dòng ngắn (2-5 ký tự)
    """
    lines = full_text.splitlines()
    # Loại bỏ dòng trống và ký tự không phải chữ/số
    clean_lines = [line.strip() for line in lines if line.strip()]

    # Lọc dòng có độ dài ngắn
    candidates = [
        line for line in clean_lines
        if 2 <= len(line) <= 5 and any(c.isalnum() for c in line)
    ]

    # Trả về dòng cuối cùng
    return candidates[-1] if candidates else "Không tìm thấy CAPTCHA"


@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        full_text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
        return full_text.strip() if full_text.strip() else "No text found"
    except Exception as e:
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)


@app.post("/extract-captcha", response_class=PlainTextResponse)
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        full_text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")

        # Lọc ra captcha từ toàn bộ text
        captcha = extract_captcha_from_text(full_text)
        return captcha
    except Exception as e:
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)


