# Context Detector — Mô tả thuật toán

Trạng thái final: module này đang được pipeline chính gọi qua
`detect_by_context(text, excluded_entities=None)`. Output của module được đưa
sang `src/merger.py`; merger mới là nơi quyết định entity cuối cùng khi có
overlap với regex detector.

## Tổng quan

`context_detector.py` là module phát hiện thực thể PII (Personally Identifiable Information)
dựa trên quy tắc ngữ cảnh (rule-based), không dùng mô hình ML. Module gồm ba detector độc lập:

| Detector | Hàm công khai | Loại thực thể |
|---|---|---|
| Tên người | `detect_name(text)` | `NAME` |
| Tên người dùng | `detect_username(text)` | `USERNAME` |
| Địa chỉ | `detect_address(text)` | `ADDRESS` |

Hàm tổng hợp `detect_by_context(text)` gọi cả ba và trả về danh sách span sắp xếp theo vị trí xuất hiện.

Mỗi span có định dạng:

```python
{
    "type":  "NAME" | "USERNAME" | "ADDRESS",
    "text":  str,   # nội dung văn bản được detect
    "start": int,   # vị trí bắt đầu trong chuỗi gốc
    "end":   int,   # vị trí kết thúc (exclusive)
}
```

---

## 1. Tách câu — `_split_sentences(text)`

Trước khi chấm điểm tên, văn bản được tách thành danh sách `(câu, offset)`.

Dấu `.` chỉ được coi là **kết thúc câu** khi **đồng thời** thỏa ba điều kiện:

1. Token kết thúc bằng `.` **không** nằm trong danh sách viết tắt đã biết (`_NO_SPLIT_ABBREVS`)
2. Phần văn bản ngay sau dấu `.` **không** bắt đầu bằng TLD (`_TLDS`)
3. Sau dấu `.` là **khoảng trắng** hoặc hết chuỗi

Dấu `!` và `?` luôn là kết thúc câu.

**Các nhóm không split:**

| Nhóm | Ví dụ |
|---|---|
| Title prefix | `Dr.` `Mr.` `Mrs.` `Ms.` `Prof.` |
| Viết tắt địa chỉ | `St.` `Rd.` `Ave.` `Apt.` `Blvd.` `Ter.` |
| Viết tắt khác | `Jr.` `Sr.` `etc.` `vs.` `e.g.` `i.e.` `Inc.` `Ltd.` |
| TLD (email/URL) | `.com` `.net` `.org` `.edu` `.vn` `.ai` ... |

---

## 2. Phát hiện tên — `detect_name(text)`

Thuật toán gồm **hai tầng** xử lý: fast path và scoring path.

### 2.1 Fast path — Trigger mạnh

Nếu văn bản chứa bất kỳ trigger nào dưới đây, tên được lấy **ngay lập tức**, không qua scoring.

**`NAME_TRIGGERS`** — trigger cứng nhất:
```
"my name is"  "full name"  "name:"
```

**`_LABEL_TRIGGERS`** — các label phổ biến theo sau bởi tên:
```
"contact person:"       "submitted by:"         "author:"
"written by:"           "signed by:"            "prepared by:"
"reported by:"          "from:"                 "sender:"
"recipient:"            "applicant:"            "client:"
"patient:"              "contact information:"  "contact info:"
"personal information:" "personal info:"        "contact details:"
"personal details:"     "user details:"         "account details:"
"full name:"            "regards,"              "sincerely,"
"best regards:"         ...
```

Sau trigger, thuật toán thu thập 1–4 token liên tiếp thỏa tất cả điều kiện:

| Điều kiện | Mô tả |
|---|---|
| Bắt đầu bằng chữ hoa | `John` ✅ `john` ❌ |
| Không chứa chữ số | `John2` ❌ |
| Không chứa ký tự đặc biệt | `john@mail` ❌ (trừ dấu `-` vì tên có thể có `Mary-Jane`) |
| Không phải stopword | `And` `The` `Is` ... ❌ |
| Không có đuôi động từ (sau token đầu) | `Working` `Graduated` `Management` ❌ |

Nếu fast path tìm được kết quả → trả về ngay, **không** vào scoring path.

### 2.2 Scoring path — Khi không có trigger

#### Bước 1: Quét candidate — `_extract_name_candidates(text)`

Quét toàn bộ văn bản tìm cụm từ viết hoa liên tiếp **(tối thiểu 2, tối đa 4 token)**.

**Các điều kiện loại ở outer loop** (trước khi bắt đầu collect một group):

| Điều kiện loại | Ví dụ |
|---|---|
| Không bắt đầu bằng chữ hoa | `the` `and` |
| Chứa ký tự đặc biệt | `john@mail` |
| Là title prefix | `Dr.` `Mr.` → strip, chuyển sang token tiếp theo |
| Là `As` đứng đầu câu | `As Mieko...` → bỏ `As`, lấy `Mieko` |
| Token trước là số nguyên | `97 Lincoln` → `Lincoln` bị loại (địa chỉ) |
| Bắt đầu bằng chữ số | `71st` |
| Là stopword | `And` `Or` `The` `Is` ... |
| Là label header word | `Information` `Details` `Witness` `Nominee` ... |

**Các điều kiện dừng collect trong group:**

| Điều kiện dừng | Ví dụ |
|---|---|
| Token không viết hoa | `and` |
| Chứa ký tự đặc biệt | |
| Là stopword / title prefix / addr abbrev | |
| Là label header word (kể cả có `:` cuối) | `Information:` |
| Là job title stopword (sau token đầu) | `Account` `Manager` `Director` ... |
| Có đuôi động từ (sau token đầu) | `Working` `Graduated` `Management` |
| Bắt đầu bằng chữ số | |

**Điều kiện loại sau khi collect xong:**
- Ít hơn 2 token → loại
- Token **cuối** nằm trong `_ORG_PLACE_SUFFIXES` → loại (tên tổ chức/địa điểm, không phải tên người)

**`_ORG_PLACE_SUFFIXES`** gồm ~70 từ:

| Nhóm | Ví dụ |
|---|---|
| Công ty / doanh nghiệp | `company` `corp` `inc` `ltd` `group` `lab` `tech` `ventures` |
| Tổ chức / cơ quan | `foundation` `institute` `association` `hospital` `council` |
| Trường học | `university` `college` `school` `academy` |
| Địa điểm / cơ sở | `hotel` `restaurant` `mall` `stadium` `bank` `airport` |

Ví dụ:
```
"Harvard University"  → cuối là "university" → loại ❌
"Intel Company"       → cuối là "company"    → loại ❌
"Kazuo Sun"           → cuối là "sun"        → giữ  ✅
```

#### Bước 2: Chấm điểm — `_score_candidate(candidate, sentence, full_text)`

Với mỗi candidate, duyệt qua từng câu (output của `_split_sentences`). Nếu câu chứa bất kỳ phần nào của candidate (partial match) thì tính điểm. **Điểm của candidate = điểm cao nhất trong tất cả các câu nó xuất hiện.**

##### Nhóm 1 — Definitive (score = 100, break ngay)

| Pattern | Ví dụ |
|---|---|
| Trigger trong `NAME_TRIGGERS` / `_LABEL_TRIGGERS` + candidate đứng ngay sau | `name: John Smith` |
| `I, [name]` hoặc `[name], I` | `I, John Smith, am a developer` |
| `I'm [name]` hoặc `I am [name]` | `I'm Kazuo Sun` |
| `I was named [name]` | `I was named Robert Johnson` |

##### Nhóm 2 — Scoring thông thường

| Tín hiệu | Điểm | Ghi chú |
|---|---|---|
| `my name` xuất hiện trong câu | +10 | |
| `As [name],` đầu câu | +5 | |
| `label: [name]` — dấu `:` đứng ngay trước candidate | +5 | Bất kỳ label nào, kể cả ngoài list |
| Appositive: `[name], <job title>,` | +3 | Từ sau dấu phẩy là job title |
| Signature: `[name]\n<job title>` | +4 | Candidate trên dòng riêng, dòng sau là chức danh |
| Đại từ ngôi 1 (`I` `me` `my`) trong câu | +2 | Nếu có cả ngôi 1 lẫn ngôi 3 → chỉ tính ngôi 1 |
| Đại từ ngôi 3 (`he` `she` `his` `her`) trong câu | +1 | Chỉ tính khi không có ngôi 1 |
| Nghề nghiệp trong cùng câu | +2 | Xem mục 2.3 |
| Tên lặp lại trong toàn đoạn (partial match) | +1/lần | Tối đa +5 |
| Title prefix (`Dr.` `Mr.` `Mrs.`...) trước tên | +1 | |

> Đại từ **không cộng dồn** nếu xuất hiện nhiều lần trong cùng một câu.

#### Bước 3: Chọn winner

| Tình huống | Hành động |
|---|---|
| Có candidate definitive (score = 100) | Trả về ngay, không so sánh tiếp |
| Chỉ 1 candidate | Trả về candidate đó dù score = 0 |
| Nhiều candidate | Chọn candidate có điểm **cao nhất** |
| Tie (cùng điểm) | Chọn candidate xuất hiện **sớm nhất** trong văn bản |
| Không có candidate nào | Trả về `[]` |

### 2.3 Phát hiện nghề nghiệp — `_has_job_in_sentence(sentence)`

Một câu được coi là có tín hiệu nghề nghiệp khi thỏa một trong hai điều kiện:

**Cách 1 — Danh sách cứng** `_JOB_HARDLIST` (~35 nghề, không phụ thuộc vị trí):
```
coach, surgeon, nurse, pilot, chef, judge, attorney, actress,
waitress, mechanic, CEO, CTO, CFO, doctor, lawyer, teacher,
developer, designer, analyst, manager, director, ...
```

**Cách 2 — Đuôi từ + role marker** (tránh false positive như `underwater`, `after`):

Từ có đuôi `-man/-men`, `-er`, `-ist`, `-ant`, `-ent`, `-or`, `-ician` chỉ được tính khi đứng ngay sau role marker:

```
a, an, the, as a, as an, is a, am a, was a,
works as, worked as, working as, ...
```

Ví dụ:
```
"I am a developer"   → role marker "a" + đuôi -er  → ✅
"went underwater"    → không có role marker trước   → ❌
```

---

## 3. Phát hiện tên người dùng — `detect_username(text)`

### Trigger

```
USERNAME_TRIGGERS = ["username", "user name", "account", "handle"]
```

`account` và `handle` là **trigger yếu** — chỉ kích hoạt khi có separator rõ ràng (`:` hoặc ` is `) ngay sau, tránh false positive như `"account manager"`.

### Quy trình

1. Tìm trigger (kiểm tra word boundary)
2. Bỏ qua khoảng trắng và separator (`:`, `is`)
3. Lấy token tiếp theo, strip dấu câu cuối
4. Kiểm tra token khớp regex:

```
@?[A-Za-z0-9_][\w.\-]*
```

| Phần | Ý nghĩa |
|---|---|
| `@?` | Dấu `@` tùy chọn |
| `[A-Za-z0-9_]` | Ký tự đầu: chữ, số, hoặc `_` (không phải `.` hay `-`) |
| `[\w.\-]*` | Các ký tự tiếp theo: chữ, số, `_`, `.`, `-` |

---

## 4. Phát hiện địa chỉ — `detect_address(text)`

### 4.1 Primary: Regex pattern

Địa chỉ được nhận diện theo cấu trúc:

```
[số nhà 1–5 chữ số] [tên đường] [loại đường] [hướng?] [đơn vị?]
```

**Số nhà:** `\b\d{1,5}(?!\d)` — 1 đến 5 chữ số, negative lookahead đảm bảo không phải một phần của số dài hơn (loại số điện thoại, zip code dài...).

**Loại đường** (sắp xếp từ dài đến ngắn để tránh match sớm):
```
Boulevard, Terrace, Avenue, Street, Circle, Drive, Court, Place,
Lane, Trail, Road, Walk, Park, Loop, Pass, Point, Run, Path,
Bend, Ridge, Hill, Square, Pines, Baron, Via,
Blvd., Ave., Ter., Rd., St., Dr., Ln., Ct., Pl.
```

**Hướng** (tùy chọn):
```
North, South, East, West, Northeast, Northwest, Southeast, Southwest
```

**Đơn vị** (tùy chọn):
```
Suite <số>, Apt. <số>, Apartment <số>, Unit <số>
```

Ví dụ detect được:

| Địa chỉ | Ghi chú |
|---|---|
| `97 Lincoln Street` | Cơ bản |
| `736 Sicard Street Southeast` | Có hướng |
| `5701 North 67th Avenue` | Hướng trước loại đường |
| `1309 Southwest 71st Terrace` | Hướng trước loại đường |
| `93110 Cynthia Walk Apt. 308` | Có đơn vị |
| `6420 Via Baron` | Loại đường đặc biệt |
| `1890 Orchard View Road` | Tên đường nhiều từ |
| `1234567 Lincoln Street` | ❌ Bị loại — số nhà > 5 chữ số |

### 4.2 Fallback: Trigger keyword

Dùng cho địa chỉ không có loại đường tiêu chuẩn:

```
ADDRESS_TRIGGERS = ["street", "road", "avenue", "district", "city",
                    "st.", "rd.", "ave."]
```

Quy trình:
1. Tìm trigger
2. Lấy clause từ dấu câu trước đến dấu câu sau
3. Strip noise words đầu clause (`at`, `is`, `the`, `located`, `live`, `reside`, ...)
4. Kiểm tra số nhà đầu clause không quá 5 chữ số
5. Kiểm tra không overlap với span đã detect ở bước primary

### 4.3 Loại trừ email

Trước khi detect, tất cả span email được xác định trước:
```
[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+
```
Bất kỳ span địa chỉ nào nằm trong span email → bỏ qua.

---

## 5. Luồng xử lý tổng thể

```
detect_by_context(text)
│
├── detect_name(text)
│   │
│   ├── [Fast path] Quét NAME_TRIGGERS + _LABEL_TRIGGERS
│   │   └── Tìm thấy → thu thập token → trả về ngay
│   │
│   └── [Scoring path] Không có trigger
│       ├── _split_sentences(text)
│       │     └── Tách câu, tránh split nhầm tại abbrev/TLD
│       ├── _extract_name_candidates(text)
│       │     ├── Outer loop: lọc title prefix, As, stopword,
│       │     │               label header word, số đứng trước
│       │     ├── Inner loop: dừng tại stopword, job title,
│       │     │               verb suffix, org/place suffix
│       │     └── Loại nếu < 2 token hoặc cuối là org/place suffix
│       ├── _score_candidate(cand, sent, text) × mỗi (candidate, câu)
│       │     ├── Definitive check (→ break nếu score = 100)
│       │     └── Scoring: label colon, appositive, signature,
│       │                  pronoun, job, repeat, title prefix
│       └── Chọn winner: điểm cao nhất, tie → sớm nhất
│
├── detect_username(text)
│   └── Duyệt USERNAME_TRIGGERS → word boundary → regex match
│
└── detect_address(text)
    ├── Xác định email spans
    ├── [Primary]  _ADDRESS_RE.finditer(text)
    └── [Fallback] ADDRESS_TRIGGERS → clause extraction
```

---

## 6. Bảng hằng số quan trọng

| Hằng số | Mô tả | Số lượng |
|---|---|---|
| `NAME_TRIGGERS` | Trigger cứng nhất cho tên | 3 |
| `_LABEL_TRIGGERS` | Label phổ biến trước tên | ~25 |
| `_NAME_STOPWORDS` | Từ dừng loại khỏi token tên | ~50 |
| `_LABEL_HEADER_WORDS` | Từ header viết hoa không phải tên | ~25 |
| `_ORG_PLACE_SUFFIXES` | Suffix tổ chức/địa điểm loại khỏi candidate | ~70 |
| `_JOB_TITLE_STOPWORDS` | Chức danh dừng collect group | ~20 |
| `_JOB_HARDLIST` | Nghề nghiệp dạng danh sách cứng | ~35 |
| `_TITLE_PREFIXES` | Prefix tước hiệu strip khỏi tên | 10 |
| `_NO_SPLIT_ABBREVS` | Viết tắt không tách câu | ~25 |
| `_TLDS` | Top-level domain không tách câu | ~20 |
| `_STREET_TYPES` | Loại đường trong regex địa chỉ | ~30 |
| `_VERB_SUFFIX_RE` | Regex đuôi động từ | `(ing\|tion\|sion\|ment\|ed\|ness)` |
| `_SPECIAL_CHARS_RE` | Ký tự đặc biệt loại token | `[~!@#$%^&*()...]` (trừ `-`) |
