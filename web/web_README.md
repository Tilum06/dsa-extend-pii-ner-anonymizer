# Local Web Demo

Thư mục `web/` chứa giao diện web local dùng để demo hệ thống nhận diện và ẩn danh thông tin cá nhân trong văn bản.

Web này cho phép người dùng nhập một đoạn văn bản, nhấn nút xử lý, sau đó hệ thống sẽ gọi API backend để phát hiện các thông tin PII và trả về văn bản đã được gắn nhãn hoặc ẩn danh.

## Mục tiêu

Local web demo giúp trực quan hóa kết quả của hệ thống rule-based PII detection.

Thay vì chỉ chạy chương trình bằng terminal, người dùng có thể nhập văn bản trực tiếp trên trình duyệt và xem kết quả xử lý ngay trên giao diện web.

Ví dụ:

```text
Input:
My name is John Smith and my email is john@gmail.com.

Output:
My name is [NAME] and my email is [EMAIL].
```

## Chức năng chính

Web demo gồm các chức năng:

1. Nhập văn bản thô từ người dùng.
2. Gửi văn bản đến backend thông qua API.
3. Backend gọi các module xử lý PII trong thư mục `src/`.
4. Hiển thị văn bản đã được ẩn danh.
5. Hiển thị danh sách entity được phát hiện, bao gồm:
   - Loại entity
   - Nội dung entity
   - Vị trí bắt đầu
   - Vị trí kết thúc

## Cấu trúc thư mục

```text
web/
  app.py
  templates/
    index.html
  static/
    style.css
    script.js
  README.md
```

Ý nghĩa từng file:

| File | Vai trò |
|---|---|
| `app.py` | Backend Flask, định nghĩa route web và API |
| `templates/index.html` | Giao diện chính của website |
| `static/style.css` | Định dạng giao diện |
| `static/script.js` | Gửi request đến API và hiển thị kết quả |
| `README.md` | Mô tả cách chạy và sử dụng web demo |

## Luồng xử lý

```text
Người dùng nhập text
        |
        v
Frontend gọi API /api/detect
        |
        v
Backend Flask nhận text
        |
        v
Gọi regex_detector.py
        |
        v
Gọi context_detector.py
        |
        v
Gộp entity bằng merger.py
        |
        v
Ẩn danh text bằng anonymizer.py
        |
        v
Trả kết quả về frontend
        |
        v
Hiển thị tagged text và bảng entity
```

## API chính

### `GET /`

Route này dùng để mở giao diện web.

Ví dụ:

```text
http://127.0.0.1:5000
```

### `POST /api/detect`

Route này dùng để nhận văn bản từ frontend và trả về kết quả phát hiện PII.

#### Request body

```json
{
  "text": "My name is John Smith and my email is john@gmail.com."
}
```

#### Response body

```json
{
  "original_text": "My name is John Smith and my email is john@gmail.com.",
  "tagged_text": "My name is [NAME] and my email is [EMAIL].",
  "entities": [
    {
      "type": "NAME",
      "text": "John Smith",
      "start": 11,
      "end": 21
    },
    {
      "type": "EMAIL",
      "text": "john@gmail.com",
      "start": 38,
      "end": 52
    }
  ]
}
```

## Liên kết với các module trong `src/`

Web backend không tự xử lý thuật toán, mà chỉ gọi lại các module đã có trong project.

Các module được sử dụng:

```text
src/regex_detector.py
src/context_detector.py
src/merger.py
src/anonymizer.py
```

Trong đó:

| Module | Chức năng |
|---|---|
| `regex_detector.py` | Phát hiện EMAIL, PHONE, URL |
| `context_detector.py` | Phát hiện NAME, USERNAME, ADDRESS |
| `merger.py` | Gộp kết quả và xử lý overlap |
| `anonymizer.py` | Thay PII bằng nhãn tương ứng |

## Cài đặt thư viện

Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

Nếu chưa có Flask, thêm dòng sau vào `requirements.txt`:

```text
flask
```

Sau đó chạy lại:

```bash
pip install -r requirements.txt
```

## Cách chạy web demo

Từ thư mục gốc của project, chạy:

```bash
python web/app.py
```

Sau đó mở trình duyệt và truy cập:

```text
http://127.0.0.1:5000
```

## Ví dụ sử dụng

### Input

```text
My name is John Smith. You can contact me at john@gmail.com or +84 912 345 678.
```

### Output

```text
My name is [NAME]. You can contact me at [EMAIL] or [PHONE].
```

### Detected entities

```json
[
  {
    "type": "NAME",
    "text": "John Smith",
    "start": 11,
    "end": 21
  },
  {
    "type": "EMAIL",
    "text": "john@gmail.com",
    "start": 45,
    "end": 59
  },
  {
    "type": "PHONE",
    "text": "+84 912 345 678",
    "start": 63,
    "end": 79
  }
]
```

## Quy ước dữ liệu

Mỗi entity được trả về theo format chuẩn của project:

```json
{
  "type": "EMAIL",
  "text": "john@gmail.com",
  "start": 12,
  "end": 26
}
```

Trong đó:

| Trường | Ý nghĩa |
|---|---|
| `type` | Loại PII, ví dụ `NAME`, `EMAIL`, `PHONE` |
| `text` | Chuỗi PII được phát hiện |
| `start` | Vị trí ký tự bắt đầu trong văn bản gốc |
| `end` | Vị trí kết thúc, không bao gồm ký tự tại vị trí `end` |

Các loại entity hợp lệ:

```text
NAME
EMAIL
PHONE
ADDRESS
USERNAME
URL
```

## Ghi chú khi phát triển

- Frontend chỉ có nhiệm vụ nhập text và hiển thị kết quả.
- Backend chịu trách nhiệm gọi các module xử lý trong `src/`.
- Không viết lại thuật toán detection trong JavaScript.
- Không thay đổi format entity chuẩn `type`, `text`, `start`, `end`.
- Nếu không phát hiện được entity nào, API trả về danh sách rỗng `[]`.
- Text gốc chỉ được thay đổi ở bước anonymization.

## Hướng phát triển thêm

Có thể mở rộng web demo với các chức năng sau:

1. Highlight entity trực tiếp trong văn bản.
2. Cho phép chọn chế độ masking:
   - `[EMAIL]`
   - `[PII]`
   - `***`
3. Hiển thị số lượng entity theo từng loại.
4. Cho phép upload file `.txt`.
5. Xuất kết quả ra file JSON hoặc CSV.
6. Hiển thị bảng so sánh giữa prediction và ground truth.
7. Thêm giao diện đánh giá Precision, Recall, F1-score.

## Vai trò trong project

Phần web local là lớp giao diện demo cho hệ thống. Nó không thay thế phần thuật toán chính, mà chỉ giúp người dùng kiểm thử nhanh và trình bày kết quả trực quan hơn.

Pipeline chính của project vẫn là:

```text
Input text
-> Rule-based detection
-> Merge entities
-> Anonymization
-> Evaluation
```
