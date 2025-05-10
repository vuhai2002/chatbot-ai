# AI Chatbot Q&A for Documents

## Giới thiệu

Hệ thống API cho phép người dùng tải lên các định dạng tài liệu (PDF, Word, TXT), tự động phân tích và chuyển đổi thành dạng vector embedding, sau đó cho phép truy vấn thông tin từ các tài liệu này bằng ngôn ngữ tự nhiên.

## Tính năng chính

- Upload nhiều định dạng tài liệu (PDF, DOCX, TXT)
- Phân tích ngữ nghĩa văn bản bằng OpenAI Embeddings
- Trả lời câu hỏi dựa trên nội dung tài liệu đã tải lên
- Quản lý tài liệu (upload, list, delete)
- Tìm kiếm ngữ nghĩa (semantic search) trong tài liệu

## Kiến trúc hệ thống

- **FastAPI**: Backend API framework
- **OpenAI**: Embedding và Q&A
- **Firebase Storage**: Lưu trữ tài liệu gốc
- **FAISS/ChromaDB**: Vector DB lưu trữ embedding
- **PostgreSQL**: Database lưu metadata tài liệu

## Cài đặt

### Yêu cầu

- Python 3.8+
- PostgreSQL
- Firebase project (tùy chọn)

### Bước cài đặt

1. Clone repository:
```bash
git clone https://github.com/yourusername/chatbot-ai-ecolaundry.git
cd chatbot-ai-ecolaundry
```

2. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Cài đặt thư viện:
```bash
pip install "pip<24" # Hạ phiên bản pip xuống < 24 (khuyên dùng)

pip install -r requirements.txt
```

4. Tạo file `.env` (sao chép từ `.env.example`):
```
OPENAI_API_KEY=your_openai_api_key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatbot_db
FIREBASE_CREDENTIALS=path/to/firebase-credentials.json
FIREBASE_BUCKET=your-firebase-bucket.appspot.com
VECTOR_DB=faiss  # or chroma
```

5. Khởi chạy ứng dụng:
```bash
python main.py

uvicorn app.main:app --reload
```

Ứng dụng sẽ chạy tại http://localhost:8000

## API Endpoints

### Upload tài liệu

```
POST /documents/upload
```

Yêu cầu:
- Form data với key `file`
- Hỗ trợ: PDF, DOCX, TXT
- Giới hạn: 10MB

Phản hồi:
```json
{
  "message": "Upload thành công",
  "file_id": "..."
}
```

### Đặt câu hỏi

```
POST /ask
```

Yêu cầu:
```json
{
  "question": "Câu hỏi của bạn?",
  "file_id": "optional-file-id",  // tùy chọn
  "max_tokens": 1000,  // tùy chọn
  "similarity_threshold": 0.7,  // tùy chọn
  "top_k": 3  // tùy chọn
}
```

Phản hồi:
```json
{
  "answer": "Câu trả lời cho câu hỏi của bạn..."
}
```

### Liệt kê tài liệu

```
GET /documents
```

Phản hồi:
```json
{
  "documents": [
    {
      "file_id": "...",
      "filename": "document.pdf",
      "upload_time": "2023-11-01T15:30:00",
      "file_size": 1024000,
      "file_type": ".pdf"
    }
  ]
}
```

### Xóa tài liệu

```
DELETE /documents/{file_id}
```

Phản hồi:
```json
{
  "message": "Xoá thành công"
}
```

## Ghi chú

- Hệ thống sử dụng OpenAI API, nên cần API key hợp lệ
- Firebase Storage là tùy chọn nhưng được khuyến nghị để lưu trữ tài liệu gốc
- Chọn FAISS hoặc ChromaDB làm vector database tùy theo nhu cầu
