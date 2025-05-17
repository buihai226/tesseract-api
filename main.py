from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np

app = FastAPI()


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Chuyển ảnh sang đen trắng để OCR tốt hơn
    """
    img_cv = np.array(image)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)


def extract_captcha_from_text(text: str) -> str:
    """
    Tìm dòng chứa 'Nhập captcha*' và lấy 2 ký tự đầu tiên ở dòng sau
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        if "nhập captcha" in line.lower():
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                return next_line[:2] if len(next_line) >= 2 else next_line
            else:
                return "Không tìm thấy dòng sau captcha"

    return "Không tìm thấy captcha"


@app.post("/extract-all-text", response_class=PlainTextResponse)
async def extract_all_text(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        full_text = pytesseract.image_to_string(image, lang="vie", config="--psm 6")
        return full_text.strip() if full_text.strip() else "Không phát hiện văn bản nào"
    except Exception as e:
        return PlainTextResponse(f"Lỗi: {str(e)}", status_code=500)


@app.post("/extract-captcha")
async def extract_captcha(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # OCR toàn bộ văn bản
        full_text = pytesseract.image_to_string(image, lang="vie", config="--psm 6")

        # Tách CAPTCHA dựa vào dòng "Nhập captcha*"
        captcha_text = extract_captcha_from_text(full_text)

        return JSONResponse(content={
            "captcha_text": captcha_text,
            "full_text": full_text
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
