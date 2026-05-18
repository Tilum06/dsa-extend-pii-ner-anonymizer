# Pipeline Documentation

Project dùng rule-based string matching để phát hiện và ẩn danh PII. Không có bước training ML/DL.

## Entity Format

Mọi module trao đổi entity theo format:

```json
{
  "type": "EMAIL",
  "text": "john@example.com",
  "start": 12,
  "end": 28
}
```

`start` và `end` là offset ký tự trong text gốc. `end` là exclusive.

## Module Flow

```text
data/raw/pii_dataset.csv
-> src.preprocessing
-> data/processed/processed_data.json
-> src.regex_detector
-> src.context_detector
-> src.merger
-> src.anonymizer
-> src.evaluator
-> results/
```

## Modules

### `src/preprocessing.py`

Đọc CSV gốc, parse các cột dạng list như `tokens` và `labels`, chuẩn hóa text, chuyển BIO labels thành ground truth entity spans.

Hàm chính:

- `load_raw_dataset`
- `parse_list_cell`
- `normalize_text`
- `map_bio_label`
- `bio_labels_to_entities`
- `build_processed_record`
- `build_processed_dataset`
- `save_processed_dataset`

### `src/regex_detector.py`

Phát hiện entity có cấu trúc rõ ràng:

- `EMAIL`
- `PHONE`
- `URL`
- `DATE`

Module chạy email và URL trước, sau đó chạy phone với exclusion spans để tránh bắt nhầm số bên trong email/URL.

Hàm public:

- `detect_email`
- `detect_phone`
- `detect_url`
- `detect_date`
- `detect_regex_entities`

### `src/context_detector.py`

Phát hiện entity phụ thuộc ngữ cảnh:

- `NAME`
- `ORGANIZATION`
- `LOCATION`
- `USERNAME`
- `ADDRESS`

NAME dùng trigger mạnh và scoring theo câu. ORGANIZATION và LOCATION dùng proper-noun candidates với scoring theo suffix/trigger; LOCATION có priority thấp hơn ADDRESS khi overlap. USERNAME dùng keyword như `username`, `handle`, `account`. ADDRESS ưu tiên regex số nhà + loại đường và có fallback bằng keyword địa chỉ.

Hàm public:

- `detect_name`
- `detect_organization`
- `detect_location`
- `detect_username`
- `detect_address`
- `detect_by_context`

### `src/merger.py`

Gộp output từ detector và loại overlap. Đây là module test chính của project.

Priority:

```text
EMAIL > URL > PHONE > DATE > ADDRESS > ORGANIZATION > LOCATION > NAME > USERNAME
```

Hàm public:

- `resolve_overlaps`
- `merge_entities`

### `src/anonymizer.py`

Thay entity spans bằng placeholder:

```text
John Smith -> [NAME]
john@example.com -> [EMAIL]
```

Hàm public:

- `anonymize_text`
- `build_token_entity_list`
- `build_token_entity_dict`

### `src/evaluator.py`

Đánh giá entity-level exact match. Một prediction đúng khi `type`, `start`, và `end` giống ground truth.

Hàm public:

- `compute_precision_recall_f1`
- `evaluate_predictions`

### `src/main.py`

Entry point chạy pipeline cuối cùng từ `data/processed/processed_data.json` và ghi output vào `results/`.

Output:

- `results/predictions.json`
- `results/anonymized_output.json`
- `results/evaluation_result.csv`

## Commands

Preprocess:

```bash
python scripts/run_preprocessing.py --input data/raw/pii_dataset.csv --output data/processed/processed_data.json
```

Run full pipeline:

```bash
python -m src.main
```

Run merger tests:

```bash
pytest tests/test_merger.py
```

Build Docker image:

```bash
docker build -t pii-ner-anonymizer .
```

Run pipeline in Docker:

```bash
docker run --rm -v "%cd%/results:/app/results" pii-ner-anonymizer
```
