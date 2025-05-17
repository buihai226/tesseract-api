FROM python:3.10-slim

# Cài các gói hệ thống và tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean

# Copy mã nguồn
WORKDIR /app
COPY . .

# Cài thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Chạy server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
