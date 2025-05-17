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
    Tiền xử lý ảnh để cải thiện nhận diện OCR, đặc biệt với text màu đỏ trên nền trắng
    """
    img_cv = np.array(image)
    
    # Chuyển sang thang độ xám và tập trung vào kênh đỏ để làm nổi bật text màu đỏ
    channels = cv2.split(img_cv)
    red_channel = channels[2]  # Kênh đỏ
    gray = cv2.subtract(255, red_channel)  # Đảo ngược để text đỏ thành sáng trên nền tối
    
    # Áp dụng threshold để làm nổi bật text
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 5
    )
    
    # Loại bỏ nhiễu
    thresh = cv2.medianBlur(thresh, 3)
    
    # Resize ảnh lên 4 lần để tăng độ chi tiết cho OCR
    thresh = cv2.resize(thresh, (thresh.shape[1] * 4, thresh.shape[0] * 4), interpolation=cv2.INTER_CUBIC)
    
    return Image.fromarray(thresh)

def crop_captcha_region(image: Image.Image) -> Image.Image:
    """
    Cắt vùng chứa captcha dựa trên bố cục cố định của ảnh
    """
    img_cv = np.array(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # Áp dụng threshold để làm nổi bật viền khung captcha
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Tìm các đường viền (contours)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Tìm khung hình chữ nhật chứa captcha
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Lọc dựa trên kích thước và vị trí (captcha thường nằm ở vùng dưới bên phải)
        if 50 < w < 150 and 20 < h < 60 and y > img_cv.shape[0] * 0.5:
            return image.crop((x, y, x + w, y + h))
    
    # Nếu không tìm thấy, trả về ảnh gốc
    return image

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

        # Cắt vùng chứa captcha
        captcha_region = crop_captcha_region(image)

        # Tiền xử lý vùng captcha trước khi OCR
        processed_image = preprocess_for_ocr(captcha_region)

        # OCR vùng captcha
        captcha_text = pytesseract.image_to_string(
            processed_image, 
            lang="eng",  # Chỉ cần tiếng Anh vì captcha là chữ và số
            config="--psm 10 --oem 1 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        ).strip()

        # Làm sạch captcha text
        captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)

        if not captcha_text:
            return JSONResponse(content={"error": "Không tìm thấy captcha trong ảnh"}, status_code=400)

        return JSONResponse(content={
            "captcha_text": captcha_text,
            "image_size": image.size
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)