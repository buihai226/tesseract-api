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
    Tiền xử lý ảnh để cải thiện nhận diện OCR, chuyển về kênh màu đỏ để làm nổi bật text
    """
    img_cv = np.array(image)
    
    # Tách kênh màu và tập trung vào kênh đỏ để làm nổi bật text màu đỏ (như "r3")
    channels = cv2.split(img_cv)
    red_channel = channels[2]  # Kênh đỏ
    gray = cv2.subtract(255, red_channel)  # Đảo ngược để text đỏ thành sáng trên nền tối
    
    # Áp dụng adaptive threshold để làm nổi bật text
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 3
    )
    
    # Loại bỏ nhiễu
    thresh = cv2.medianBlur(thresh, 3)
    
    # Dilate để làm rõ các ký tự
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    
    # Resize ảnh lên 4 lần để tăng độ chi tiết cho OCR
    thresh = cv2.resize(thresh, (thresh.shape[1] * 4, thresh.shape[0] * 4), interpolation=cv2.INTER_CUBIC)
    
    return Image.fromarray(thresh)

@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Tiền xử lý ảnh trước khi OCR
        processed_image = preprocess_for_ocr(image)

        # OCR toàn ảnh với cấu hình tối ưu
        full_text = pytesseract.image_to_string(
            processed_image, 
            lang="vie+eng", 
            config="--psm 6 --oem 1 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
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

        # OCR toàn ảnh với cấu hình tối ưu
        full_text = pytesseract.image_to_string(
            processed_image, 
            lang="vie+eng", 
            config="--psm 6 --oem 1 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )

        # Tìm đoạn text chứa "Nhập captcha" và lấy đoạn text phía sau
        lines = full_text.splitlines()
        captcha_text = None
        for i, line in enumerate(lines):
            if "Nhập captcha" in line.lower():  # Không phân biệt hoa thường
                # Tìm dòng tiếp theo có chứa ký tự alphanumeric
                for j in range(i + 1, len(lines)):
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