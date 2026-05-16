# Nhận diện và ẩn danh thông tin cá nhân trong văn bản bằng Rule-based String Matching

Đây là skeleton project Python cho bài toán phát hiện và ẩn danh thông tin cá nhân trong văn bản. Mục tiêu của dự án là xây dựng một pipeline thuần thuật toán để đọc văn bản thô, phát hiện các thực thể PII phổ biến, rồi thay thế chúng bằng nhãn tương ứng như `[NAME]`, `[EMAIL]`, `[PHONE]`.

Project tập trung vào hướng rule-based, sử dụng regular expression, keyword matching và xử lý chuỗi. Project không sử dụng machine learning hoặc deep learning, và README này mô tả khung sườn triển khai trước khi đi vào phần code chi tiết.

Về phạm vi hiện tại, hệ thống hướng tới 6 loại entity chính:

- NAME
- EMAIL
- PHONE
- ADDRESS
- USERNAME
- URL

Dataset chính là `data/raw/pii_dataset.csv`, được lấy từ Kaggle PII External Dataset. Sau khi kiểm tra file CSV dùng trong project, dataset có 4434 dòng và 16 cột, trong đó các cột quan trọng nhất là `document`, `text`, `tokens`, `trailing_whitespace` và `labels`.

## Mục tiêu

Xây dựng hệ thống phát hiện và ẩn danh các thông tin định danh cá nhân trong văn bản, bao gồm 6 loại entity:

- NAME
- EMAIL
- PHONE
- ADDRESS
- USERNAME
- URL

Lưu ý: `O` không phải là entity cần phát hiện. Trong BIO tagging, `O` chỉ có nghĩa là token không thuộc bất kỳ entity nào.

Hệ thống nhận đầu vào là văn bản thô, phát hiện các thực thể PII bằng luật thủ công, sau đó thay thế các thông tin này bằng nhãn tương ứng.

Ví dụ:

```text
Input:
My name is John Smith and my email is john@gmail.com.

Output:
My name is [NAME] and my email is [EMAIL].
```

## Vì sao không dùng Machine Learning / Deep Learning

Project này phục vụ mục tiêu học thuật về thuật toán xử lý chuỗi. Vì vậy, project không sử dụng các thư viện huấn luyện mô hình như scikit-learn, PyTorch, TensorFlow, Keras, spaCy, transformers hoặc CRF libraries.

Thay vào đó, hệ thống sử dụng các kỹ thuật:

- Regular Expression
- Pattern Matching
- Keyword Matching
- Token Scanning
- Rule-based Detection
- Greedy Interval Selection
- Exact Span Matching

Dataset có sẵn nhãn BIO, nhưng nhãn này chỉ dùng để tạo ground truth và đánh giá kết quả. Project không dùng nhãn để train mô hình.

## Schema dataset

File `pii_dataset.csv` có các cột sau:

```text
document
text
tokens
trailing_whitespace
labels
prompt
prompt_id
name
email
phone
job
address
username
url
hobby
len
```

Các cột cần dùng trực tiếp trong pipeline:

| Cột | Vai trò |
|---|---|
| `document` | ID hoặc mã định danh của sample |
| `text` | Văn bản gốc |
| `tokens` | Danh sách token trong văn bản |
| `trailing_whitespace` | Thông tin khoảng trắng sau token, nếu cần khôi phục span |
| `labels` | Danh sách nhãn BIO tương ứng với `tokens` |

Các cột `name`, `email`, `phone`, `address`, `username`, `url` là thông tin PII được sinh sẵn trong từng sample. Có thể dùng để inspect dữ liệu, nhưng ground truth chính nên được tạo từ `tokens` và `labels`.

Các cột không dùng làm entity chính trong phiên bản hiện tại:

| Cột | Lý do |
|---|---|
| `job` | Không có nhãn BIO tương ứng trong phạm vi entity đã chọn |
| `hobby` | Không phải PII chính cần ẩn danh |
| `prompt`, `prompt_id` | Metadata tạo dữ liệu |
| `len` | Độ dài sample, chỉ dùng để thống kê nếu cần |

## Pipeline xử lý

```text
pii_dataset.csv
-> load_raw_dataset()
-> normalize_text()
-> convert BIO labels to ground truth entities
-> run regex-based detector
-> run context-based detector
-> merge detected entities
-> resolve overlapping entities
-> anonymize text
-> evaluate prediction with ground truth
-> JSON / CSV output
```

## BIO tagging

Dataset sử dụng định dạng BIO cho bài toán NER:

```text
O
B-NAME_STUDENT
I-NAME_STUDENT
B-EMAIL
B-PHONE_NUM
I-PHONE_NUM
B-STREET_ADDRESS
I-STREET_ADDRESS
B-USERNAME
B-URL_PERSONAL
```

Ý nghĩa:

- `B-X`: token bắt đầu của entity loại X
- `I-X`: token tiếp theo thuộc cùng entity loại X
- `O`: token không thuộc entity nào

Ví dụ:

```text
Token           Label
My              O
name            O
is              O
John            B-NAME_STUDENT
Smith           I-NAME_STUDENT
and             O
my              O
email           O
is              O
john@gmail.com  B-EMAIL
```

Sau khi xử lý BIO, ground truth sẽ có dạng:

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
    "start": 38,
    "end": 52
  }
]
```

## Mapping nhãn từ dataset sang project

Tên nhãn trong dataset gốc dài hơn tên entity dùng trong project. Vì vậy, bước preprocessing cần ánh xạ nhãn như sau:

| Label trong dataset | Entity dùng trong project |
|---|---|
| `B-NAME_STUDENT`, `I-NAME_STUDENT` | `NAME` |
| `B-EMAIL` | `EMAIL` |
| `B-PHONE_NUM`, `I-PHONE_NUM` | `PHONE` |
| `B-STREET_ADDRESS`, `I-STREET_ADDRESS` | `ADDRESS` |
| `B-USERNAME` | `USERNAME` |
| `B-URL_PERSONAL` | `URL` |
| `O` | Không phải entity |

Ví dụ:

```python
LABEL_MAPPING = {
    "NAME_STUDENT": "NAME",
    "EMAIL": "EMAIL",
    "PHONE_NUM": "PHONE",
    "STREET_ADDRESS": "ADDRESS",
    "USERNAME": "USERNAME",
    "URL_PERSONAL": "URL",
}
```

Khi đọc label BIO, cần bỏ tiền tố `B-` hoặc `I-`, sau đó dùng bảng mapping trên để đổi sang entity chuẩn của project.

## Phân công công việc

| Thành viên | Công việc chính | File phụ trách |
|---|---|---|
| Người 1 | Dataset preprocessing, chuyển BIO labels thành ground truth entities | `src/preprocessing.py` |
| Người 2 | Nhận diện EMAIL, PHONE, URL bằng regex | `src/regex_detector.py` |
| Người 3 | Nhận diện NAME, USERNAME, ADDRESS bằng rule ngữ cảnh | `src/context_detector.py` |
| Người 4 | Gộp kết quả, xử lý overlap, ẩn danh, chạy demo | `src/merger.py`, `src/anonymizer.py`, `web/app.py` |

## Vai trò từng thành viên

### Người 1: Dataset preprocessing

Người 1 phụ trách chuẩn bị dữ liệu đầu vào và đáp án đúng cho toàn bộ hệ thống.

Nhiệm vụ:

- Đọc file `pii_dataset.csv`
- Lấy các cột cần thiết: `document`, `text`, `tokens`, `trailing_whitespace`, `labels`
- Chuyển chuỗi biểu diễn list trong `tokens` và `labels` thành list Python
- Chuẩn hóa văn bản nếu cần
- Chuyển BIO labels thành danh sách ground truth entities
- Ánh xạ label gốc sang entity chuẩn của project
- Xuất dữ liệu đã xử lý ra `data/processed/processed_data.json`

Output mẫu:

```json
{
  "id": 1,
  "text": "My name is John Smith and my email is john@gmail.com.",
  "tokens": ["My", "name", "is", "John", "Smith", "and", "my", "email", "is", "john@gmail.com"],
  "ground_truth": [
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

### Người 2: Regex-based detector

Người 2 phụ trách nhận diện các PII có cấu trúc rõ ràng:

- EMAIL
- PHONE
- URL

Các loại này phù hợp với regular expression vì có mẫu chuỗi tương đối cố định.

Ví dụ:

```python
email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
phone_pattern = r"(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}"
url_pattern = r"https?://\S+|www\.\S+"
```

Với PHONE, sau khi regex bắt được chuỗi ứng viên, nên kiểm tra thêm:

- Tổng số chữ số thường nằm trong khoảng 9 đến 15
- Không nằm bên trong EMAIL
- Không nằm bên trong URL
- Không bắt nhầm một phần của địa chỉ hoặc mã số quá ngắn

Output mẫu:

```json
[
  {
    "type": "EMAIL",
    "text": "john@gmail.com",
    "start": 38,
    "end": 52
  }
]
```

### Người 3: Context-based detector

Người 3 phụ trách các PII khó hơn, cần kết hợp keyword, ngữ cảnh và token scanning:

- NAME
- USERNAME
- ADDRESS

Ví dụ rule cho NAME:

```text
Nếu gặp cụm mạnh như "my name is", "full name", "name:"
-> kiểm tra các token phía sau
-> nếu token bắt đầu bằng chữ hoa và không chứa số
-> gom 1 đến 4 token liên tiếp thành NAME
```

Lưu ý: các cụm yếu như `I am` dễ gây false positive, vì câu như `I am happy` hoặc `I am studying Computer Science` không phải lúc nào cũng chứa tên người. Nếu dùng `I am`, cần thêm điều kiện kiểm tra chặt hơn.

Ví dụ rule cho ADDRESS:

```text
Nếu gặp số nhà
-> quét các token phía sau
-> nếu có keyword như Street, Road, Avenue, District, City, St., Rd., Ave.
-> gán cụm đó là ADDRESS
```

Ví dụ rule cho USERNAME:

```text
Nếu gặp keyword như "username", "user name", "account", "handle"
-> kiểm tra token phía sau
-> nếu token có dạng chữ/số/gạch dưới hoặc bắt đầu bằng @
-> gán token đó là USERNAME
```

Output mẫu:

```json
[
  {
    "type": "NAME",
    "text": "John Smith",
    "start": 11,
    "end": 21
  },
  {
    "type": "ADDRESS",
    "text": "123 Nguyen Trai Street",
    "start": 65,
    "end": 88
  }
]
```

### Người 4: Integration, anonymization and demo

Người 4 phụ trách ghép toàn bộ project thành hệ thống hoàn chỉnh.

Nhiệm vụ:

- Gộp kết quả từ người 2 và người 3
- Xử lý entity bị trùng hoặc chồng lấn
- Thay PII bằng nhãn tương ứng
- Xuất file kết quả
- Duy trì web demo và script detection

Ví dụ xử lý overlap:

```text
john@gmail.com -> EMAIL
john -> USERNAME
```

Vì `john` nằm trong `john@gmail.com`, hệ thống giữ entity dài hơn hoặc entity có độ ưu tiên cao hơn.

Thứ tự ưu tiên khi overlap:

```text
EMAIL > URL > PHONE > ADDRESS > NAME > USERNAME
```

## Cấu trúc thư mục

```text
pii_rule_based_detection/
  data/
    raw/
      pii_dataset.csv
    processed/
      processed_data.json

  src/
    preprocessing.py
    regex_detector.py
    context_detector.py
    merger.py
    anonymizer.py
    config.py

  scripts/
    inspect_dataset.py
    run_preprocessing.py
    run_detection.py

  tests/
    test_preprocessing.py
    test_regex_detector.py
    test_context_detector.py
    test_merger.py
    test_anonymizer.py

  results/
    anonymized_output.json

  notebooks/
    demo.ipynb

  report/
    report.tex
    figures/
    references.bib

  README.md
  requirements.txt
```

## Input/Output chuẩn cho từng module

Để các thành viên code song song mà không bị lệch format, toàn bộ project dùng chung một chuẩn entity như sau:

```json
{
  "type": "EMAIL",
  "text": "john@gmail.com",
  "start": 38,
  "end": 52
}
```

| Trường | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `type` | string | Loại PII, ví dụ `EMAIL`, `PHONE`, `NAME` |
| `text` | string | Chuỗi được phát hiện trong văn bản |
| `start` | int | Vị trí ký tự bắt đầu trong văn bản gốc |
| `end` | int | Vị trí ký tự kết thúc, không bao gồm ký tự tại vị trí `end` |

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

### 1. Module `preprocessing.py`

Module này do người 1 phụ trách.

Nhiệm vụ:

```text
Dataset gốc -> dữ liệu đã xử lý + ground truth entities
```

#### Input

File dữ liệu gốc:

```text
data/raw/pii_dataset.csv
```

Một dòng dữ liệu gốc có thể có dạng:

```json
{
  "document": 1,
  "text": "My name is John Smith and my email is john@gmail.com.",
  "tokens": ["My", "name", "is", "John", "Smith", "and", "my", "email", "is", "john@gmail.com"],
  "labels": ["O", "O", "O", "B-NAME_STUDENT", "I-NAME_STUDENT", "O", "O", "O", "O", "B-EMAIL"]
}
```

#### Output

File dữ liệu đã xử lý:

```text
data/processed/processed_data.json
```

Format chuẩn:

```json
[
  {
    "id": 1,
    "text": "My name is John Smith and my email is john@gmail.com.",
    "tokens": ["My", "name", "is", "John", "Smith", "and", "my", "email", "is", "john@gmail.com"],
    "ground_truth": [
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
]
```

#### Hàm chính

```python
def load_raw_dataset(path: str) -> list[dict]:
    pass

def normalize_text(text: str) -> str:
    pass

def map_bio_label(label: str) -> str | None:
    pass

def convert_bio_to_entities(text: str, tokens: list[str], labels: list[str]) -> list[dict]:
    pass

def build_processed_dataset(raw_data: list[dict]) -> list[dict]:
    pass

def save_processed_data(data: list[dict], output_path: str) -> None:
    pass
```

Ví dụ output của `convert_bio_to_entities()`:

```python
[
    {
        "type": "NAME",
        "text": "John Smith",
        "start": 11,
        "end": 21
    }
]
```

### 2. Module `regex_detector.py`

Module này do người 2 phụ trách.

Nhiệm vụ:

```text
Text -> EMAIL, PHONE, URL entities
```

#### Input

Một sample đã xử lý từ `processed_data.json`:

```json
{
  "id": 1,
  "text": "Contact me at john@gmail.com or +84 912 345 678.",
  "tokens": ["Contact", "me", "at", "john@gmail.com", "or", "+84", "912", "345", "678"],
  "ground_truth": []
}
```

#### Output

Danh sách entity phát hiện được bằng regex:

```json
[
  {
    "type": "EMAIL",
    "text": "john@gmail.com",
    "start": 14,
    "end": 28
  },
  {
    "type": "PHONE",
    "text": "+84 912 345 678",
    "start": 32,
    "end": 48
  }
]
```

#### Hàm chính

```python
def detect_email(text: str) -> list[dict]:
    pass

def detect_phone(text: str) -> list[dict]:
    pass

def detect_url(text: str) -> list[dict]:
    pass

def detect_regex_entities(text: str) -> list[dict]:
    pass
```

Ví dụ:

```python
text = "Contact me at john@gmail.com or visit https://example.com."

detect_regex_entities(text)
```

Output:

```python
[
    {
        "type": "EMAIL",
        "text": "john@gmail.com",
        "start": 14,
        "end": 28
    },
    {
        "type": "URL",
        "text": "https://example.com",
        "start": 38,
        "end": 57
    }
]
```

### 3. Module `context_detector.py`

Module này do người 3 phụ trách.

Nhiệm vụ:

```text
Text + tokens -> NAME, USERNAME, ADDRESS entities
```

#### Input

Một sample đã xử lý từ `processed_data.json`:

```json
{
  "id": 2,
  "text": "My name is John Smith. I live at 123 Nguyen Trai Street.",
  "tokens": ["My", "name", "is", "John", "Smith", ".", "I", "live", "at", "123", "Nguyen", "Trai", "Street"],
  "ground_truth": []
}
```

#### Output

Danh sách entity phát hiện bằng rule ngữ cảnh:

```json
[
  {
    "type": "NAME",
    "text": "John Smith",
    "start": 11,
    "end": 21
  },
  {
    "type": "ADDRESS",
    "text": "123 Nguyen Trai Street",
    "start": 33,
    "end": 56
  }
]
```

#### Hàm chính

```python
def detect_name(text: str, tokens: list[str]) -> list[dict]:
    pass

def detect_username(text: str, tokens: list[str]) -> list[dict]:
    pass

def detect_address(text: str, tokens: list[str]) -> list[dict]:
    pass

def detect_context_entities(text: str, tokens: list[str]) -> list[dict]:
    pass
```

Ví dụ:

```python
text = "My name is John Smith. My username is john_smith22."
tokens = ["My", "name", "is", "John", "Smith", ".", "My", "username", "is", "john_smith22", "."]

detect_context_entities(text, tokens)
```

Output:

```python
[
    {
        "type": "NAME",
        "text": "John Smith",
        "start": 11,
        "end": 21
    },
    {
        "type": "USERNAME",
        "text": "john_smith22",
        "start": 38,
        "end": 50
    }
]
```

### 4. Module `merger.py`

Module này do người 4 phụ trách.

Nhiệm vụ:

```text
Regex entities + context entities -> final entities
```

Module này dùng để gộp kết quả từ người 2 và người 3, đồng thời xử lý các entity bị trùng hoặc chồng lấn.

#### Input

Output từ `regex_detector.py`:

```python
regex_entities = [
    {
        "type": "EMAIL",
        "text": "john@gmail.com",
        "start": 12,
        "end": 26
    }
]
```

Output từ `context_detector.py`:

```python
context_entities = [
    {
        "type": "USERNAME",
        "text": "john",
        "start": 12,
        "end": 16
    }
]
```

#### Output

Danh sách entity cuối cùng:

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

Trong ví dụ trên, `USERNAME` bị loại vì nằm bên trong `EMAIL`.

#### Hàm chính

```python
def is_overlap(entity_a: dict, entity_b: dict) -> bool:
    pass

def choose_better_entity(entity_a: dict, entity_b: dict) -> dict:
    pass

def resolve_overlaps(entities: list[dict]) -> list[dict]:
    pass

def merge_entities(regex_entities: list[dict], context_entities: list[dict]) -> list[dict]:
    pass
```

Rule đề xuất khi overlap:

```text
1. Nếu priority khác nhau, chọn entity có priority cao hơn.
2. Nếu priority bằng nhau, chọn entity dài hơn.
3. Nếu vẫn bằng nhau, chọn entity xuất hiện trước trong văn bản.
```

Priority:

```text
EMAIL > URL > PHONE > ADDRESS > NAME > USERNAME
```

### 5. Module `anonymizer.py`

Module này do người 4 phụ trách.

Nhiệm vụ:

```text
Text + final entities -> anonymized text
```

#### Input

```python
text = "My name is John Smith and my email is john@gmail.com."

entities = [
    {"type": "NAME", "text": "John Smith", "start": 11, "end": 21},
    {"type": "EMAIL", "text": "john@gmail.com", "start": 38, "end": 52}
]
```

#### Output

```python
"My name is [NAME] and my email is [EMAIL]."
```

#### Hàm chính

```python
def anonymize_text(text: str, entities: list[dict]) -> str:
    pass
```

Lưu ý: nên thay thế từ cuối văn bản về đầu văn bản để không làm lệch chỉ số `start` và `end`.

Pseudo-code:

```text
Sort entities by start position in descending order
For each entity:
    Replace text[entity.start:entity.end] with "[" + entity.type + "]"
Return anonymized text
```

## Quy ước chung khi code

Tất cả module cần tuân theo các quy ước sau:

1. Không tự ý đổi tên trường `type`, `text`, `start`, `end`.
2. `start` và `end` luôn tính theo vị trí ký tự trong văn bản gốc.
3. `end` là vị trí kết thúc, không bao gồm ký tự tại vị trí `end`.
4. Mỗi detector luôn trả về `list[dict]`, kể cả khi không tìm thấy gì.
5. Nếu không tìm thấy entity nào, trả về list rỗng `[]`.
6. Không module nào được sửa trực tiếp `text` gốc, trừ `anonymizer.py`.
7. Ground truth chỉ được tạo từ `preprocessing.py`.
8. Không đưa `O` vào danh sách entity dự đoán hoặc ground truth.
9. Tên entity cuối cùng chỉ dùng 6 giá trị: `NAME`, `EMAIL`, `PHONE`, `ADDRESS`, `USERNAME`, `URL`.

## Ví dụ chạy xuyên suốt một sample

Input từ `processed_data.json`:

```json
{
  "id": 1,
  "text": "My name is John Smith and my email is john@gmail.com.",
  "tokens": ["My", "name", "is", "John", "Smith", "and", "my", "email", "is", "john@gmail.com"],
  "ground_truth": [
    {"type": "NAME", "text": "John Smith", "start": 11, "end": 21},
    {"type": "EMAIL", "text": "john@gmail.com", "start": 38, "end": 52}
  ]
}
```

Output từ `regex_detector.py`:

```json
[
  {"type": "EMAIL", "text": "john@gmail.com", "start": 38, "end": 52}
]
```

Output từ `context_detector.py`:

```json
[
  {"type": "NAME", "text": "John Smith", "start": 11, "end": 21}
]
```

Output sau `merger.py`:

```json
[
  {"type": "NAME", "text": "John Smith", "start": 11, "end": 21},
  {"type": "EMAIL", "text": "john@gmail.com", "start": 38, "end": 52}
]
```

Output sau `anonymizer.py`:

```text
My name is [NAME] and my email is [EMAIL].
```

## Mô tả các file chính

### `src/preprocessing.py`

Chứa các hàm xử lý dữ liệu ban đầu:

```python
def load_raw_dataset(path):
    pass

def normalize_text(text):
    pass

def map_bio_label(label):
    pass

def convert_bio_to_entities(text, tokens, labels):
    pass

def build_processed_dataset(raw_data):
    pass

def save_processed_data(data, output_path):
    pass
```

### `src/regex_detector.py`

Chứa các hàm nhận diện PII bằng regex:

```python
def detect_email(text):
    pass

def detect_phone(text):
    pass

def detect_url(text):
    pass

def detect_regex_entities(text):
    pass
```

### `src/context_detector.py`

Chứa các hàm nhận diện PII bằng rule ngữ cảnh:

```python
def detect_name(text, tokens):
    pass

def detect_username(text, tokens):
    pass

def detect_address(text, tokens):
    pass

def detect_context_entities(text, tokens):
    pass
```

### `src/merger.py`

Chứa các hàm gộp và xử lý overlap:

```python
def is_overlap(entity_a, entity_b):
    pass

def choose_better_entity(entity_a, entity_b):
    pass

def resolve_overlaps(entities):
    pass

def merge_entities(regex_entities, context_entities):
    pass
```

### `src/anonymizer.py`

Chứa hàm thay thế PII bằng nhãn:

```python
def anonymize_text(text, entities):
    pass
```

Ví dụ:

```text
John Smith -> [NAME]
john@gmail.com -> [EMAIL]
```

## Chuẩn bị môi trường

Cài thư viện:

```bash
pip install -r requirements.txt
```

File `requirements.txt` có thể gồm:

```text
pandas
numpy
tqdm
pytest
```

Nếu chỉ dùng thư viện chuẩn Python và `pandas`, không cần cài thêm thư viện ML.

## Inspect dataset

Dùng script này để kiểm tra cấu trúc file dữ liệu:

```bash
python scripts/inspect_dataset.py --input data/raw/pii_dataset.csv
```

Script nên in ra:

```text
- Số dòng dữ liệu
- Danh sách cột
- Một vài sample đầu tiên
- Kiểu dữ liệu của cột tokens và labels
- Danh sách nhãn BIO xuất hiện trong dataset
- Số lượng từng loại nhãn
```

## Chạy preprocessing

```bash
python scripts/run_preprocessing.py \
  --input data/raw/pii_dataset.csv \
  --output data/processed/processed_data.json
```

Output:

```text
data/processed/processed_data.json
```

## Chạy detection

```bash
python scripts/run_detection.py \
  --input data/processed/processed_data.json \
  --output results/predictions.json
```

Output:

```text
results/predictions.json
```

## Chạy test

```bash
pytest tests/
```

Nên viết test tối thiểu cho các phần:

- Convert BIO labels to entity spans
- Detect EMAIL
- Detect PHONE
- Detect URL
- Detect NAME bằng context mạnh
- Detect ADDRESS bằng keyword
- Detect USERNAME
- Resolve overlap giữa EMAIL và USERNAME
- Anonymize theo thứ tự từ cuối về đầu
- Evaluate exact match

## Output dự kiến

### `predictions.json`

```json
[
  {
    "id": 1,
    "predicted_entities": [
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
]
```

### `anonymized_output.json`

```json
[
  {
    "id": 1,
    "original_text": "My name is John Smith and my email is john@gmail.com.",
    "anonymized_text": "My name is [NAME] and my email is [EMAIL]."
  }
]
```

## Evaluation

Hệ thống đánh giá theo entity-level matching.

Một prediction được xem là đúng khi:

```text
predicted type == gold type
predicted span == gold span
```

Các chỉ số:

```text
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1-score  = 2 * Precision * Recall / (Precision + Recall)
```

Trong đó:

- TP: entity dự đoán đúng
- FP: entity dự đoán nhưng không có trong ground truth
- FN: entity có trong ground truth nhưng hệ thống bỏ sót

Do project dùng rule-based method, exact match có thể làm điểm thấp nếu entity bị lệch span nhỏ. Vì vậy, có thể báo cáo thêm partial match để phân tích lỗi, nhưng điểm chính vẫn nên dùng exact match.

## Thuật toán chính

Project gồm các thuật toán chính:

1. Convert BIO Labels to Entity Spans
2. Regex-based Email Detection
3. Regex-based Phone Detection and Validation
4. Regex-based URL Detection
5. Context-based Name Detection
6. Username Detection using Keyword and Pattern Matching
7. Address Detection using Keyword Matching
8. Overlap Resolution using Greedy Selection
9. Text Anonymization by Reverse-order Replacement
10. Entity-level Evaluation

## Hạn chế hiện tại

- Rule-based method khó nhận diện chính xác NAME và ADDRESS trong nhiều ngữ cảnh phức tạp
- Regex có thể bỏ sót các format email, phone hoặc URL hiếm gặp
- Có thể nhầm username với một phần của email
- Dataset chủ yếu là tiếng Anh, chưa tối ưu cho tiếng Việt
- Không có khả năng tự học từ dữ liệu mới
- Kết quả phụ thuộc nhiều vào chất lượng rule thủ công
- Entity-level exact match khá nghiêm ngặt, chỉ cần lệch span nhỏ cũng bị tính sai

## Hướng phát triển

1. Bổ sung thêm rule cho phone number theo từng quốc gia
2. Cải thiện address detector bằng danh sách keyword mở rộng
3. Thêm dictionary cho first name, last name và địa danh
4. Thêm fuzzy matching cho các biến thể viết tắt như `St.`, `Rd.`, `Ave.`
5. Tối ưu overlap resolution bằng interval scheduling
6. Thêm giao diện web local để visualize kết quả
7. Mở rộng sang dữ liệu tiếng Việt
8. Thêm chế độ masking khác nhau: `[PII]`, `[EMAIL]`, hoặc giữ một phần thông tin
9. Viết thêm test case cho từng detector
10. Xuất báo cáo thống kê lỗi sai theo từng entity type
