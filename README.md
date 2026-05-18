# Rule-based PII NER Anonymizer

Project phát hiện và ẩn danh thông tin cá nhân trong văn bản bằng rule-based string matching. Hệ thống không dùng machine learning hoặc deep learning.

## Trạng thái hiện tại

Project đã được đóng gói về trạng thái final:

- Pipeline chính chạy qua `python -m src.main` hoặc `python main.py`.
- Tài liệu module nằm trong `docs/pipeline.md`.
- Test suite chỉ tập trung vào `src/merger.py` để kiểm tra chất lượng gộp entity và performance tổng thể.
- Dockerfile đã được thêm để build và chạy pipeline trong container.
- Các nhánh code demo/legacy và function chưa dùng rõ ràng đã được dọn khỏi runtime chính.

## Entity hỗ trợ

```text
NAME
EMAIL
PHONE
ADDRESS
ORGANIZATION
LOCATION
USERNAME
URL
```

Mọi entity dùng chung schema:

```json
{
  "type": "EMAIL",
  "text": "john@example.com",
  "start": 12,
  "end": 28
}
```

## Pipeline

```text
data/raw/pii_dataset.csv
-> preprocessing
-> data/processed/processed_data.json
-> regex detector
-> context detector
-> merger
-> anonymizer
-> evaluator
-> results/
```

Module chính:

| Module | Vai trò |
|---|---|
| `src/preprocessing.py` | Đọc CSV, parse token/label, tạo ground truth từ BIO labels |
| `src/tokenizer.py` | Tokenize text bằng whitespace split |
| `src/regex_detector.py` | Detect `EMAIL`, `PHONE`, `URL` |
| `src/context_detector.py` | Detect `NAME`, `ORGANIZATION`, `LOCATION`, `USERNAME`, `ADDRESS` bằng rule ngữ cảnh |
| `src/merger.py` | Gộp entity, xử lý trùng và overlap |
| `src/anonymizer.py` | Thay PII bằng placeholder như `[EMAIL]` |
| `src/evaluator.py` | Tính precision, recall, F1 bằng exact-span match |
| `src/main.py` | Chạy full pipeline |

Xem chi tiết từng module tại [docs/pipeline.md](docs/pipeline.md).

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy preprocessing

```bash
python scripts/run_preprocessing.py --input data/raw/pii_dataset.csv --output data/processed/processed_data.json
```

## Chạy full pipeline

```bash
python -m src.main
```

Hoặc:

```bash
python main.py
```

Output:

```text
results/predictions.json
results/anonymized_output.json
results/evaluation_result.csv
```

## Test

Project hiện chỉ test merger:

```bash
pytest tests/test_merger.py
```

Merger là điểm quyết định output cuối cùng vì nó nhận kết quả từ nhiều detector, xử lý overlap, áp priority và trả về entity list sạch.

Priority khi overlap:

```text
EMAIL > URL > PHONE > ADDRESS > ORGANIZATION > LOCATION > NAME > USERNAME
```

## Docker

Build image:

```bash
docker build -t pii-ner-anonymizer .
```

Run pipeline:

```bash
docker run --rm -v "%cd%/results:/app/results" pii-ner-anonymizer
```

Trên PowerShell, lệnh mount tương đương:

```powershell
docker run --rm -v ${PWD}/results:/app/results pii-ner-anonymizer
```

Container mặc định chạy:

```bash
python -m src.main
```

## Web demo

Web demo vẫn nằm trong `web/` và có thể chạy riêng:

```bash
python web/app.py
```

Mặc định Flask chạy tại:

```text
http://127.0.0.1:5000
```
