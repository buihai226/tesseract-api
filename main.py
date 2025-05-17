from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse
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


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Chuyển ảnh sang ảnh đen trắng (threshold) để Tesseract đọc tốt hơn
    """
    img_cv = np.array(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

def crop_captcha_region(image: Image.Image) -> Image.Image:
    """
    Cắt vùng CAPTCHA theo tỉ lệ ảnh — dùng được với mọi độ phân giải
    """
    width, height = image.size
    # Toạ độ theo phần trăm (chuẩn theo ảnh gốc 1080x1920)
    x1 = int(width * 0.605)
    y1 = int(height * 0.567)
    x2 = int(width * 0.70)
    y2 = int(height * 0.588)
    return image.crop((x1, y1, x2, y2))

@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        # Đọc ảnh upload
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # OCR toàn ảnh
        full_text = pytesseract.image_to_string(image, lang="vie", config="--psm 6")
        return full_text.strip() if full_text.strip() else "Không phát hiện văn bản nào"
    except Exception as e:
        return PlainTextResponse(f"Lỗi: {str(e)}", status_code=500)

@app.post("/extract-captcha")
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        original_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Cắt vùng captcha
        captcha_img = crop_captcha_region(original_image)

        # Tiền xử lý ảnh
        processed = preprocess_for_ocr(captcha_img)

        # OCR với cấu hình tối ưu cho captcha
        captcha_text = pytesseract.image_to_string(
            processed,
            lang="vie",
            config="--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        ).strip()

        return JSONResponse(content={
            "captcha_text": captcha_text,
            "image_size": original_image.size
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


