# Tokenization Module

## 1. Mục đích

Module tokenizer được xây dựng để tách văn bản thô trong cột `text` thành danh sách token.

Trong dataset gốc `pii_dataset.csv`, đã có sẵn cột `tokens`. Tuy nhiên, khi hệ thống chạy thực tế, input thường chỉ là một đoạn văn bản thô, không có sẵn danh sách token. Vì vậy, project cần một module tokenize riêng để xử lý dữ liệu đầu vào.

Module này nhận dữ liệu từ file:

```text
data/raw/pii_text.csv
```

và tạo ra file:

```text
data/processed/tokenized.csv
```

## 2. Input

File input là `pii_text.csv`.

File này chỉ giữ lại các cột cần thiết cho bước tokenize, ví dụ:

```csv
document,text
1,"My name is John Smith and my email is john@gmail.com."
2,"Contact me at +84 912 345 678."
```

Trong đó:

| Cột | Ý nghĩa |
|---|---|
| `document` | ID của sample |
| `text` | Văn bản gốc cần tokenize |

File này không cần các cột như `labels`, `prompt`, `name`, `email`, `phone`, `job`, `address`, `username`, `url`, `hobby`, `len`.

## 3. Output

Sau khi chạy tokenizer, chương trình tạo ra file:

```text
data/processed/tokenized.csv
```

Output có dạng:

```csv
document,text,tokens
1,"My name is John Smith and my email is john@gmail.com.","['My', 'name', 'is', 'John', 'Smith', 'and', 'my', 'email', 'is', 'john@gmail.com.']"
2,"Contact me at +84 912 345 678.","['Contact', 'me', 'at', '+84', '912', '345', '678.']"
```

Trong đó:

| Cột | Ý nghĩa |
|---|---|
| `document` | ID của sample |
| `text` | Văn bản gốc |
| `tokens` | Danh sách token được tạo ra từ cột `text` |

## 4. Cách tokenize đã thực hiện

Tokenizer hiện tại sử dụng phương pháp tách token theo khoảng trắng.

Cụ thể, với mỗi dòng dữ liệu:

```python
tokens = text.split()
```

Điều này có nghĩa là văn bản được tách thành token dựa trên các ký tự khoảng trắng như dấu cách, tab hoặc xuống dòng.

Ví dụ:

```python
text = "My name is John Smith"
tokens = text.split()
```

Kết quả:

```python
["My", "name", "is", "John", "Smith"]
```

## 5. Vì sao dùng `text.split()`

Sau khi kiểm tra dataset gốc, cột `tokens` trong `pii_dataset.csv` có cách tách gần giống hoàn toàn với whitespace tokenization.

Ví dụ, dấu câu không bị tách riêng ra khỏi từ đứng trước:

```text
Input:
My name is John Smith.

Output tokens:
["My", "name", "is", "John", "Smith."]
```

Không phải:

```text
["My", "name", "is", "John", "Smith", "."]
```

Một ví dụ khác:

```text
Input:
My name is Popova, and I am a student.

Output tokens:
["My", "name", "is", "Popova,", "and", "I", "am", "a", "student."]
```

Ở đây:

```text
Popova,   -> dấu phẩy vẫn dính với token
student.  -> dấu chấm vẫn dính với token
```

Vì vậy, dùng `text.split()` là hợp lý nếu mục tiêu là tạo output giống cột `tokens` trong dataset gốc.

## 6. Hàm chính trong `src/tokenizer.py`

File chính:

```text
src/tokenizer.py
```

Các hàm chính:

```python
def tokenize_text(text: str) -> list[str]:
    return text.split()
```

Hàm này nhận một chuỗi văn bản và trả về danh sách token.

Ví dụ:

```python
tokenize_text("My email is john@gmail.com.")
```

Output:

```python
["My", "email", "is", "john@gmail.com."]
```

Ngoài ra, module có thể có hàm xử lý cả file CSV:

```python
def tokenize_csv(input_path: str, output_path: str) -> None:
    ...
```

Hàm này thực hiện các bước:

```text
1. Đọc file CSV input
2. Lấy cột text
3. Tokenize từng dòng bằng tokenize_text()
4. Ghi kết quả ra file tokenized.csv
```

## 7. Script chạy tokenizer

File chạy:

```text
scripts/run_tokenizer.py
```

Lệnh chạy:

```powershell
python scripts/run_tokenizer.py --input data/raw/pii_text.csv --output data/processed/tokenized.csv
```

Trong đó:

| Tham số | Ý nghĩa |
|---|---|
| `--input` | Đường dẫn tới file text thô |
| `--output` | Đường dẫn tới file CSV sau khi tokenize |

Ví dụ:

```powershell
python scripts/run_tokenizer.py --input data/raw/pii_text.csv --output data/processed/tokenized.csv
```

Sau khi chạy thành công, file output sẽ nằm tại:

```text
data/processed/tokenized.csv
```

## 8. Cấu trúc thư mục liên quan

Cấu trúc đề xuất:

```text
Extend/
├── data/
│   ├── raw/
│   │   ├── pii_dataset.csv
│   │   └── pii_text.csv
│   └── processed/
│       └── tokenized.csv
├── src/
│   ├── __init__.py
│   └── tokenizer.py
├── scripts/
│   └── run_tokenizer.py
└── tests/
    └── compare_tokens.py
```

Ý nghĩa:

| File | Vai trò |
|---|---|
| `data/raw/pii_text.csv` | File input chỉ gồm `document`, `text` |
| `src/tokenizer.py` | Module tokenize chính |
| `scripts/run_tokenizer.py` | Script chạy tokenizer từ terminal |
| `data/processed/tokenized.csv` | File output sau khi tokenize |
| `tests/compare_tokens.py` | Script test so sánh token mới với token gốc |

## 9. Kiểm tra kết quả tokenize

Để kiểm tra tokenizer có tạo token giống dataset gốc hay không, dùng file:

```text
tests/compare_tokens.py
```

Lệnh chạy:

```powershell
python tests/compare_tokens.py --original data/raw/pii_dataset.csv --tokenized data/processed/tokenized.csv
```

Trong đó:

| Tham số | Ý nghĩa |
|---|---|
| `--original` | File dataset gốc có cột `tokens` |
| `--tokenized` | File mới được tạo bởi tokenizer |

Nếu tokenizer hoạt động tốt, terminal sẽ in kết quả tương tự:

```text
TOKEN COMPARISON RESULT
Original file : data/raw/pii_dataset.csv
Tokenized file: data/processed/tokenized.csv
Rows compared : 4434
Matched rows  : 4434 (100.00%)
Different rows: 0 (0.00%)

Result: PASS - All token columns are identical.
```

Nếu có dòng khác nhau, chương trình sẽ in ra vị trí khác biệt đầu tiên:

```text
Document ID   : ...
Original len  : ...
Tokenized len : ...
First diff at token index: ...
Original token : ...
Tokenized token: ...
Original context :
[...]

Tokenized context:
[...]
```

Thông tin này giúp biết tokenizer bị lệch ở dòng nào và token nào.

## 10. Vai trò của tokenizer trong pipeline

Pipeline sau khi thêm tokenizer:

```text
pii_text.csv
-> tokenizer
-> tokenized.csv
-> detector
-> merger
-> anonymizer
-> evaluator
```

Cụ thể:

```text
text thô
-> tokenize_text()
-> tokens
-> detect entity
```

Module tokenizer không có nhiệm vụ nhận diện PII. Nó chỉ chuẩn bị danh sách token để các module sau sử dụng.

## 11. Lưu ý quan trọng

### 11.1. Tokenizer không dùng cột `tokens` có sẵn

Trong quá trình tokenize, chương trình chỉ dùng cột:

```text
text
```

Không sử dụng cột `tokens` của dataset gốc.

Cột `tokens` gốc chỉ dùng để kiểm tra lại kết quả trong bước test.

### 11.2. Dấu câu vẫn dính với từ

Vì dùng `text.split()`, dấu câu sẽ không bị tách riêng.

Ví dụ:

```text
hello.
```

sẽ thành:

```python
["hello."]
```

không phải:

```python
["hello", "."]
```

Điều này là chủ ý, vì dataset gốc cũng đang tokenize theo cách tương tự.

### 11.3. Email và URL không bị tách nhỏ

Ví dụ:

```text
john@gmail.com
```

sẽ thành:

```python
["john@gmail.com"]
```

Không bị tách thành:

```python
["john", "@", "gmail", ".", "com"]
```

Điều này thuận lợi cho bước regex detector vì email và URL vẫn giữ nguyên dạng chuỗi đầy đủ.

### 11.4. Phone number có thể bị tách thành nhiều token

Ví dụ:

```text
+84 912 345 678
```

sẽ thành:

```python
["+84", "912", "345", "678"]
```

Điều này không ảnh hưởng nhiều đến regex detector nếu detector làm việc trực tiếp trên `text` gốc thay vì chỉ dựa vào token.

## 12. Hạn chế của tokenizer hiện tại

Tokenizer hiện tại đơn giản và dễ kiểm tra, nhưng có một số hạn chế:

```text
- Không tách riêng dấu câu.
- Không chuẩn hóa email, phone, URL.
- Không xử lý nâng cao với dấu ngoặc, dấu gạch nối hoặc ký tự đặc biệt.
- Phone number có khoảng trắng sẽ bị tách thành nhiều token.
- Không phù hợp nếu muốn token-level BIO tagging mới hoàn toàn.
```

Tuy nhiên, với mục tiêu hiện tại là tạo output giống cột `tokens` trong dataset gốc, cách dùng `text.split()` là phù hợp.

## 13. Hướng mở rộng

Nếu sau này muốn tokenizer mạnh hơn, có thể thay bằng regex tokenizer.

Ví dụ:

```python
import re

TOKEN_PATTERN = re.compile(
    r"https?://\S+|www\.\S+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+?\d[\d\s().-]{7,}\d|[A-Za-z]+|\d+|[^\w\s]"
)

def tokenize_text(text: str) -> list[str]:
    return [match.group(0) for match in TOKEN_PATTERN.finditer(text)]
```

Tuy nhiên, nếu dùng regex tokenizer thì kết quả có thể không còn giống cột `tokens` gốc trong dataset nữa. Khi đó cần cập nhật lại test và có thể phải căn chỉnh lại nhãn BIO.

Vì vậy, phiên bản hiện tại giữ cách tokenize bằng:

```python
text.split()
```

để đảm bảo tính nhất quán với dataset gốc.

## 14. Tóm tắt

Module tokenizer thực hiện các bước chính:

```text
1. Nhận file pii_text.csv gồm document và text
2. Đọc từng dòng text
3. Tokenize bằng text.split()
4. Ghi kết quả vào tokenized.csv
5. So sánh với cột tokens gốc trong pii_dataset.csv để kiểm tra độ giống nhau
```

Kết quả mong muốn:

```text
Tokenizer tạo ra cột tokens giống với dataset gốc.
```
