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


@app.post("/extract-captcha", response_class=PlainTextResponse)
async def extract_captcha(file: UploadFile = File(...)):
    try:
        
        image_bytes = await file.read()

        
        npimg = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        captcha_region = img[1080:1150, 635:775]

        gray = cv2.cvtColor(captcha_region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

        # Chuyển ngược về PIL Image để dùng với pytesseract
        captcha_image = Image.fromarray(thresh)

        # OCR: chỉ cho phép chữ và số
        text = pytesseract.image_to_string(
            captcha_image,
            lang='eng',
            config='--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )

        return text.strip() if text.strip() else "No CAPTCHA detected"
    except Exception as e:
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)

