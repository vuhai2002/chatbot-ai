FROM python:3.11

WORKDIR /app

# 1) Hạ pip xuống <24.1 để nó chấp nhận metadata "extract-msg (<=0.29.*)"
RUN pip install --upgrade "pip<24.1"

# 2) Cài các thư viện hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3) Copy requirements và cài Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# 5) Tạo thư mục cần thiết
RUN mkdir -p /app/data/vectordb /app/logs

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]