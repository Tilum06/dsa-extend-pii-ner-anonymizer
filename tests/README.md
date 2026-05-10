# Tests

Thư mục `tests/` chứa các testcase dùng để kiểm thử từng module trong project.  
Mục tiêu của phần test là giúp các thành viên có thể code song song, kiểm tra đúng input/output của từng file mà không cần đợi toàn bộ pipeline hoàn thành.

## 1. Cài đặt thư viện test

Project sử dụng `pytest` để chạy testcase.

Cài các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

Trong `requirements.txt` cần có:

```txt
pytest
```

Nếu chưa có, thêm `pytest` vào file `requirements.txt`.

## 2. Cấu trúc thư mục test

```text
tests/
  README.md
  fixtures/
    sample_processed_data.json
    sample_regex_output.json
    sample_context_output.json
    sample_final_entities.json

  test_preprocessing.py
  test_regex_detector.py
  test_context_detector.py
  test_merger.py
  test_anonymizer.py
  test_evaluator.py
  test_integration.py
```

Trong đó:

| File | Mục đích |
|---|---|
| `fixtures/` | Chứa dữ liệu mẫu dùng chung cho các test |
| `test_preprocessing.py` | Test module xử lý dữ liệu ban đầu |
| `test_regex_detector.py` | Test module nhận diện EMAIL, PHONE, URL |
| `test_context_detector.py` | Test module nhận diện NAME, USERNAME, ADDRESS |
| `test_merger.py` | Test module gộp entity và xử lý overlap |
| `test_anonymizer.py` | Test module ẩn danh văn bản |
| `test_evaluator.py` | Test module đánh giá Precision, Recall, F1 |
| `test_integration.py` | Test luồng xử lý toàn bộ pipeline |

## 3. Cách chạy toàn bộ test

Đứng tại thư mục gốc của project, chạy:

```bash
pytest tests/
```

Hoặc chạy ngắn gọn:

```bash
pytest
```

Nếu tất cả đúng, terminal sẽ hiện dạng:

```text
10 passed
```

Nếu có lỗi, terminal sẽ hiện file test bị lỗi và dòng bị lỗi.

## 4. Cách chạy test cho từng module

### Test preprocessing

```bash
pytest tests/test_preprocessing.py
```

Dùng để kiểm tra các hàm trong:

```text
src/preprocessing.py
```

Ví dụ các hàm cần test:

```python
load_raw_dataset()
parse_list_cell()
normalize_text()
map_bio_label()
bio_labels_to_entities()
build_processed_record()
save_processed_dataset()
```

### Test regex detector

```bash
pytest tests/test_regex_detector.py
```

Dùng để kiểm tra các hàm trong:

```text
src/regex_detector.py
```

Ví dụ các hàm cần test:

```python
detect_email()
detect_phone()
detect_url()
detect_regex_entities()
```

### Test context detector

```bash
pytest tests/test_context_detector.py
```

Dùng để kiểm tra các hàm trong:

```text
src/context_detector.py
```

Ví dụ các hàm cần test:

```python
detect_name()
detect_username()
detect_address()
detect_context_entities()
```

### Test merger

```bash
pytest tests/test_merger.py
```

Dùng để kiểm tra các hàm trong:

```text
src/merger.py
```

Ví dụ các hàm cần test:

```python
is_overlap()
choose_better_entity()
resolve_overlaps()
merge_entities()
```

### Test anonymizer

```bash
pytest tests/test_anonymizer.py
```

Dùng để kiểm tra hàm trong:

```text
src/anonymizer.py
```

Ví dụ hàm cần test:

```python
anonymize_text()
```

### Test evaluator

```bash
pytest tests/test_evaluator.py
```

Dùng để kiểm tra các hàm trong:

```text
src/evaluator.py
```

Ví dụ các hàm cần test:

```python
match_entity()
compute_precision_recall_f1()
evaluate_predictions()
```

### Test integration

```bash
pytest tests/test_integration.py
```

Dùng để kiểm tra luồng xử lý đầy đủ:

```text
text
-> regex detector
-> context detector
-> merger
-> anonymizer
-> evaluator
```

## 5. Quy ước dữ liệu test

Tất cả entity trong test phải dùng chung format:

```json
{
  "type": "EMAIL",
  "text": "john@gmail.com",
  "start": 12,
  "end": 26
}
```

Ý nghĩa:

| Trường | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `type` | string | Loại entity: `NAME`, `EMAIL`, `PHONE`, `ADDRESS`, `USERNAME`, `URL` |
| `text` | string | Chuỗi entity được phát hiện |
| `start` | int | Vị trí bắt đầu trong văn bản gốc |
| `end` | int | Vị trí kết thúc, không bao gồm ký tự tại vị trí `end` |

Ví dụ:

```text
My email is john@gmail.com.
            ^             ^
            start=12      end=26
```

Entity tương ứng:

```json
{
  "type": "EMAIL",
  "text": "john@gmail.com",
  "start": 12,
  "end": 26
}
```

## 6. Nguyên tắc viết testcase

Mỗi testcase nên kiểm tra một chức năng nhỏ.

Ví dụ tốt:

```python
def test_detect_email():
    text = "Contact me at john@gmail.com."
    result = detect_email(text)

    assert result == [
        {
            "type": "EMAIL",
            "text": "john@gmail.com",
            "start": 14,
            "end": 28
        }
    ]
```

Ví dụ không nên:

```python
def test_everything():
    # Test quá nhiều chức năng cùng lúc
    pass
```

Nên tách riêng:

```text
test_detect_email()
test_detect_phone()
test_detect_url()
test_merge_overlap()
test_anonymize_text()
test_evaluate_predictions()
```

## 7. Vì sao cần fixtures?

`fixtures/` chứa dữ liệu mẫu để các thành viên có thể test module của mình mà không cần chờ module khác hoàn thành.

Ví dụ:

Người phụ trách `merger.py` chưa cần chờ `regex_detector.py` và `context_detector.py` xong.  
Có thể dùng sẵn dữ liệu giả:

```python
regex_entities = [
    {
        "type": "EMAIL",
        "text": "john@gmail.com",
        "start": 12,
        "end": 26
    }
]

context_entities = [
    {
        "type": "USERNAME",
        "text": "john",
        "start": 12,
        "end": 16
    }
]
```

Kết quả mong đợi:

```python
[
    {
        "type": "EMAIL",
        "text": "john@gmail.com",
        "start": 12,
        "end": 26
    }
]
```

Vì `USERNAME` nằm bên trong `EMAIL`, hệ thống giữ `EMAIL` và loại `USERNAME`.

## 8. Cách hiểu kết quả test

### Trường hợp pass

```text
================== test session starts ==================
collected 10 items

tests/test_regex_detector.py .....
tests/test_anonymizer.py ..
tests/test_evaluator.py ...

================== 10 passed ==================
```

Nghĩa là các hàm đã trả đúng output mong đợi.

### Trường hợp fail

```text
FAILED tests/test_regex_detector.py::test_detect_email
```

Nghĩa là testcase `test_detect_email` bị sai.

Ví dụ lỗi:

```text
AssertionError: assert start == 14
```

Có thể do hàm tính sai vị trí `start`.

## 9. Quy trình làm việc cho từng thành viên

Mỗi thành viên nên làm theo quy trình:

```text
1. Chạy test của file mình phụ trách
2. Xem test nào đang fail
3. Code hoặc sửa hàm tương ứng trong src/
4. Chạy lại test
5. Khi test pass thì commit và push
```

Ví dụ người làm regex detector:

```bash
pytest tests/test_regex_detector.py
```

Nếu pass:

```text
4 passed
```

thì có thể commit code.

## 10. Lưu ý khi viết code để pass test

Các module phải tuân theo quy ước sau:

1. Không đổi tên field `type`, `text`, `start`, `end`.
2. `start` và `end` luôn tính theo vị trí ký tự trong văn bản gốc.
3. `end` là vị trí kết thúc, không bao gồm ký tự tại vị trí `end`.
4. Nếu không tìm thấy entity nào, trả về list rỗng `[]`.
5. Detector không được tự sửa `text` gốc.
6. Chỉ `anonymizer.py` được tạo văn bản đã ẩn danh.
7. Chỉ `evaluator.py` tính Precision, Recall, F1-score.
8. Không đưa label `O` vào danh sách entity.
9. Entity type chỉ dùng một trong các giá trị:

```text
NAME
EMAIL
PHONE
ADDRESS
USERNAME
URL
```

## 11. Khi thêm testcase mới

Khi thêm testcase mới, cần đảm bảo:

- Tên hàm test bắt đầu bằng `test_`
- Test chỉ kiểm tra một chức năng cụ thể
- Có input rõ ràng
- Có output mong đợi rõ ràng
- Không phụ thuộc vào file lớn nếu không cần thiết

Ví dụ:

```python
def test_detect_email_returns_empty_list_when_no_email():
    text = "There is no email here."
    result = detect_email(text)

    assert result == []
```

## 12. Lệnh hay dùng

```bash
# Chạy toàn bộ test
pytest tests/

# Chạy một file test
pytest tests/test_regex_detector.py

# Chạy một testcase cụ thể
pytest tests/test_regex_detector.py::test_detect_email

# Chạy test và hiển thị chi tiết hơn
pytest -v tests/

# Dừng ngay khi gặp lỗi đầu tiên
pytest -x tests/
```
