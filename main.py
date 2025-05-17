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
    Cắt vùng CAPTCHA dựa trên tỉ lệ ảnh (không phụ thuộc độ phân giải)
    """
    width, height = image.size

    # Vùng CAPTCHA theo tỉ lệ ( nhờ AI tính )
    x1 = int(width * 0.605)   # 60.5% từ trái
    y1 = int(height * 0.567)  # 56.7% từ trên
    x2 = int(width * 0.70)    # 70.0% từ trái
    y2 = int(height * 0.588)  # 58.8% từ trên

    captcha_img = image.crop((x1, y1, x2, y2))

    # OCR CAPTCHA
    return pytesseract.image_to_string(
        captcha_img,
        lang="eng",
        config='--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ).strip()

@app.post("/extract-captcha")
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # OCR toàn ảnh
        full_text = pytesseract.image_to_string(image, lang="eng", config="--psm 6").strip()

        # OCR vùng CAPTCHA theo tỉ lệ
        captcha_text = extract_captcha_region(image)

        return JSONResponse(content={
            "image_size": image.size,
            "full_text": full_text,
            "captcha_text": captcha_text
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


