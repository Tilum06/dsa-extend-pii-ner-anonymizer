# Test Scope

Test suite kiểm tra module `src/merger.py` và một số behavior trọng yếu của `src/context_detector.py`.

Lý do: merger là điểm gom kết quả của regex detector và context detector, nên ảnh hưởng trực tiếp đến output cuối cùng của pipeline. Các test hiện tại tập trung vào:

- gộp nhiều nhóm entity
- sắp xếp theo vị trí xuất hiện
- loại entity trùng hoặc chồng lấn
- ưu tiên entity theo thứ tự `EMAIL > URL > PHONE > ADDRESS > ORGANIZATION > LOCATION > NAME > USERNAME`
- scoring ORGANIZATION/LOCATION và rule ADDRESS thắng LOCATION khi overlap
- kiểm tra performance tổng thể với input lớn

Chạy test:

```bash
pytest tests/test_merger.py tests/test_context_detector.py
```

Hoặc:

```bash
pytest
```
