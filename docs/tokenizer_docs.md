# Tokenizer

`src/tokenizer.py` chuẩn bị token cho dữ liệu thô.

## Cách hoạt động

Tokenizer dùng whitespace tokenization:

```python
text.split()
```

Cách này giữ dấu câu gắn với token đứng trước, ví dụ `Smith.` vẫn là một token. Đây là lựa chọn phù hợp với dataset hiện tại vì cột `tokens` trong `data/raw/pii_dataset.csv` cũng gần với kiểu tách theo khoảng trắng.

## Hàm chính

- `tokenize_text(text)`: nhận một chuỗi và trả về `list[str]`.
- `tokenize_records(records)`: tokenize nhiều record CSV có cột `document,text`.
- `tokenize_csv(input_path, output_path)`: đọc CSV thô và ghi CSV có thêm cột `tokens`.

## Cách chạy

```bash
python scripts/run_tokenizer.py --input data/raw/pii_text.csv --output data/processed/tokenized.csv
```

Output:

```text
data/processed/tokenized.csv
```

Tokenizer không phát hiện PII và không sửa nội dung text gốc.
