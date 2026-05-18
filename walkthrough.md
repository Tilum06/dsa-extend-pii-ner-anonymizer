# Walkthrough: Thêm Entity DATE vào Regex Detector

## Tổng quan

Thêm entity `DATE` vào pipeline regex-based PII detection. DATE được detect bằng regex trong `src/regex_detector.py`, tuân theo entity schema hiện tại (`type`, `text`, `start`, `end`) và không phá vỡ pipeline hiện tại.

## Các file đã thay đổi

### 1. `src/regex_detector.py`

**Thay đổi chính:**

- Thêm 11 regex patterns trong `DATE_PATTERNS`, chia thành 3 nhóm:
  - **Vietnamese formats**: `ngày DD tháng MM năm YYYY`, `ngày D/M/YYYY`, `tháng MM năm YYYY`, `năm YYYY`
  - **English month-name formats**: `January 2, 2024`, `2 Jan 2024`, `January 2024`, `year YYYY`
  - **ISO / numeric formats**: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, `MM/YYYY`

- Thêm function `detect_date(text)`:
  - Dùng `re.finditer` cho từng pattern trong `DATE_PATTERNS`
  - Loại bỏ candidate overlap với EMAIL, URL, hoặc **validated** PHONE spans
  - De-duplicate nội bộ: khi nhiều pattern match overlapping span, giữ match dài nhất
  - Trả về list entity dict chuẩn `{"type": "DATE", "text": ..., "start": ..., "end": ...}`

- Tích hợp `detect_date()` vào `detect_regex_entities()`:
  - Gọi `detect_date(text)` và append kết quả vào `all_entities`
  - `_resolve_regex_overlaps()` cập nhật priority: `EMAIL > URL > PHONE > DATE`

**Quyết định thiết kế quan trọng:**

`detect_date()` dùng `detect_phone()` (kết quả đã validate 9-15 digits) thay vì raw `PHONE_PATTERN` để tạo exclusion spans. Lý do: `PHONE_PATTERN` là regex rất rộng, match cả chuỗi ngắn như `"01"` (2 digits) — những chuỗi này không phải phone number hợp lệ nhưng sẽ block date detection nếu dùng raw match.

```diff
-    phone_spans = [(m.start(), m.end()) for m in PHONE_PATTERN.finditer(text)]
+    phone_results = detect_phone(text)
+    phone_spans = [(p["start"], p["end"]) for p in phone_results]
```

---

### 2. `src/config.py`

Thêm `"DATE"` vào `ENTITY_PRIORITY` giữa `PHONE` và `ADDRESS`:

```diff
 ENTITY_PRIORITY = [
     "EMAIL",
     "URL",
     "PHONE",
+    "DATE",
     "ADDRESS",
     "NAME",
     "USERNAME",
 ]
```

Thứ tự ưu tiên khi overlap: `EMAIL > URL > PHONE > DATE > ADDRESS > NAME > USERNAME`

---

### 3. `tests/test_regex_detector.py`

Thêm 26 test cases mới trong 2 class:

**`TestDetectDate`** (23 tests):
- Numeric formats: `DD/MM/YYYY`, `D/M/YYYY`, `DD-MM-YYYY`, `D-M-YY`, `YYYY-MM-DD`, `YYYY/MM/DD`, `DD.MM.YYYY`
- English month-name: `January 2, 2024`, `Jan 2, 2024`, `2 January 2024`, `2 Jan 2024`
- Vietnamese: `ngày 02 tháng 01 năm 2024`, `02 tháng 01 năm 2024`, `ngày 2/1/2024`, `tháng 01 năm 2024`
- Month/year: `01/2024`, `January 2024`
- Contextual year: `năm 2024`, `year 2024`
- False-positive guards: bare 4-digit number, date inside URL
- Schema validation: entity format, position accuracy, empty text

**`TestDetectByRegexWithDate`** (3 tests):
- DATE xuất hiện trong combined output
- EMAIL thắng DATE khi overlap
- URL thắng DATE khi overlap

## Các file KHÔNG cần thay đổi

| File | Lý do |
|---|---|
| `src/anonymizer.py` | Đã handle mọi entity type qua BIO tagging, không hardcode entity names |
| `src/merger.py` | Dùng `ENTITY_PRIORITY` từ `config.py`, đã cập nhật ở config |
| `src/main.py` | Gọi `detect_regex_entities()` — tự động bao gồm DATE |
| `src/preprocessing.py` | Chỉ xử lý BIO labels từ dataset, không liên quan |

## Kết quả test

```
pytest tests/test_regex_detector.py tests/test_merger.py -v
============================= 64 passed in 0.08s ==============================
```

- 19 test cũ (regex detector): ✅ PASS
- 26 test mới (DATE): ✅ PASS
- 19 test merger: ✅ PASS

## Ví dụ input/output

```
Input: "The deadline is 01/02/2024 or 2024-02-01."
Output:
  DATE  [ 16: 26]  '01/02/2024'
  DATE  [ 30: 40]  '2024-02-01'

Input: "Born on January 2, 2024 and graduated 2 Jan 2024."
Output:
  DATE  [  8: 23]  'January 2, 2024'
  DATE  [ 38: 48]  '2 Jan 2024'

Input: "Ngày sinh: ngày 02 tháng 01 năm 2024."
Output:
  DATE  [ 11: 36]  'ngày 02 tháng 01 năm 2024'

Input: "Published in January 2024 and 01/2024."
Output:
  DATE  [ 13: 25]  'January 2024'
  DATE  [ 30: 37]  '01/2024'

Input: "Established in năm 2024 and year 2024."
Output:
  DATE  [ 15: 23]  'năm 2024'
  DATE  [ 28: 37]  'year 2024'

Input: "The code is 2024 and ID is 1999."
Output:
  (no entities detected)

Input: "See https://example.com/2024/01/02 for details."
Output:
  URL   [  4: 34]  'https://example.com/2024/01/02'
```

## Edge cases và hạn chế

| Edge case | Hành vi |
|---|---|
| `31/13/2024` (tháng 13 không hợp lệ) | Vẫn match — không validate semantic |
| `01/02/2024` (Jan 2 hay Feb 1?) | Match nguyên chuỗi, không interpret |
| `"May I help you?"` | Không match — cần có năm theo sau (`May 2024` mới match) |
| `2024` đứng một mình | Không match — tránh false positive |
| `năm 2024` / `year 2024` | Match — có context rõ ràng |
| Date nằm trong URL | Không match — bị URL exclusion loại bỏ |
| Date trùng phone number | Không match — bị phone exclusion loại bỏ |
