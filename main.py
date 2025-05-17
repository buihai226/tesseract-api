from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np
import re

app = FastAPI()

def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Tiền xử lý ảnh để cải thiện nhận diện OCR
    """
    img_cv = np.array(image)
    
    # Chuyển sang thang độ xám
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # Làm nổi bật text bằng adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Loại bỏ nhiễu bằng Gaussian Blur
    thresh = cv2.GaussianBlur(thresh, (3, 3), 0)
    
    # Resize ảnh lên 3 lần để cải thiện OCR
    thresh = cv2.resize(thresh, (thresh.shape[1] * 3, thresh.shape[0] * 3), interpolation=cv2.INTER_LINEAR)
    
    return Image.fromarray(thresh)

@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Tiền xử lý ảnh trước khi OCR
        processed_image = preprocess_for_ocr(image)

        # OCR toàn ảnh bằng tiếng Việt
        full_text = pytesseract.image_to_string(processed_image, lang="vie", config="--psm 6 --oem 1")
        return full_text.strip() if full_text.strip() else "Không phát hiện văn bản nào"
    except Exception as e:
        return PlainTextResponse(f"Lỗi: {str(e)}", status_code=500)

@app.post("/extract-captcha")
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Tiền xử lý ảnh trước khi OCR
        processed_image = preprocess_for_ocr(image)

        # OCR toàn ảnh bằng tiếng Việt
        full_text = pytesseract.image_to_string(
            processed_image, 
            lang="vie+eng",  # Kết hợp tiếng Việt và tiếng Anh để nhận diện cả "Nhập captcha" và "r3"
            config="--psm 6 --oem 1"
        )

        # Tìm đoạn text chứa "Nhập captcha" và lấy đoạn text phía sau
        lines = full_text.splitlines()
        captcha_text = None
        for i, line in enumerate(lines):
            if "Nhập captcha" in line:
                # Lấy dòng tiếp theo sau "Nhập captcha"
                for j in range(i + 1, len(lines)):
                    # Tìm dòng tiếp theo có chứa ký tự alphanumeric
                    potential_captcha = lines[j].strip()
                    if re.search(r'[a-zA-Z0-9]', potential_captcha):
                        captcha_text = re.sub(r'[^a-zA-Z0-9]', '', potential_captcha)
                        break
                break

        if not captcha_text:
            return JSONResponse(content={"error": "Không tìm thấy captcha trong ảnh"}, status_code=400)

        return JSONResponse(content={
            "captcha_text": captcha_text,
            "image_size": image.size
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)