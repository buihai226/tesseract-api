from fastapi import FastAPI, File, UploadFile
from fastapi.responses import PlainTextResponse
from PIL import Image
import pytesseract
import io

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
async def home():
    return "OCR API is running."

@app.post("/extract-captcha", response_class=PlainTextResponse)
async def extract_text(file: UploadFile = File(...)):
    try:
        # Đọc file ảnh
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Trích xuất toàn bộ văn bản bằng pytesseract
        text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')

        # Trả về kết quả
        return text.strip() if text.strip() else "No text found in image."
    except Exception as e:
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)
