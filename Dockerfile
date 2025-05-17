FROM python:3.10-slim

# Cài các thư viện hệ thống cần thiết cho OpenCV và Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    libgl1 \
    && apt-get clean

WORKDIR /app
COPY . .

# Cài thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
