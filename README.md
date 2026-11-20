# AI Data Analyst Agent - Hệ Thống Phân Tích Dữ Liệu Doanh Nghiệp (Tích Hợp Google Gemini API)

Dự án AI Agent hoàn chỉnh được thiết kế theo đúng **sơ đồ quy trình (Flowchart)** phân tích dữ liệu kinh doanh cho doanh nghiệp, được trang bị **Google Gemini API** (mô hình `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`):

```
[Nhập link Google Sheet / File Excel, CSV, XLSX + Bối cảnh Doanh nghiệp]
                               │
                               ▼
                       [Kiểm tra đúng?]
                          /        \
                       (No)        (Yes)
                        │            │
                        ▼            ▼
                 [Báo lỗi ND]     [Cleaning]
                        │            │
                 (Bắt nhập lại)      ▼
                        │       [Kiểm tra?]
                        │          /     \
                        │       (No)     (Yes)
                        │        │         │
                        └────────┘         ▼
                                       [Process (Gemini AI)] <────┐
                                           │                      │
                                           ▼                      │
                                        [Verify]                  │
                                           │                      │
                                           ▼                      │
                                       [Xác nhận?]                │
                                         /     \                  │
                                      (Yes)    (No)               │
                                        │        │                │
                                        │        ▼                │
                                        │    [Feedback] ──────────┘
                                        ▼
                       [Xuất file báo cáo, file excel (dạng HTML)]
                                        │
                                        ▼
                                    [Kết thúc]
```

---

## 🌟 1. Điểm Mới: Tích Hợp Google Gemini API

Hệ thống kết nối trực tiếp với **Google Gemini API** thông qua REST Client tối ưu, không yêu cầu cài đặt thêm thư viện nặng:
- **Đóng vai trò Chief Data Officer (CDO)**: Tiếp nhận toàn bộ bối cảnh doanh nghiệp và số liệu thống kê (KPIs, Pareto 80/20, xu hướng thời gian, kênh bán) để viết bản tóm tắt điều hành sắc sảo (Executive Summary).
- **Giải đáp trực diện câu hỏi bối cảnh**: Trả lời chính xác những bài toán nan giải mà doanh nghiệp đề ra trong phần nhập bối cảnh.
- **Đề xuất kế hoạch hành động chiến lược**: Phân kỳ theo Ngắn hạn (1-2 tuần), Trung hạn (1-3 tháng) và Dài hạn (6 tháng).
- **Vòng lặp Feedback thông minh**: Khi người dùng nhập góp ý điều chỉnh, Gemini tự động tái cấu trúc phân tích theo đúng phản hồi của người dùng.
- **Chế độ Dual-Engine thông minh**: Nếu người dùng chưa nhập API Key, hệ thống tự động chạy trên **Local Analytical Engine** có sẵn, đảm bảo không bao giờ bị gián đoạn.

---

## 🔑 2. Cách Lấy & Cấu Hình Gemini API Key

1. **Lấy API Key Miễn Phí**:
   - Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Đăng nhập tài khoản Google và bấm **"Create API key"**.

2. **Cách Sử Dụng Trong Ứng Dụng**:
   - **Cách 1 (Nhanh nhất)**: Nhập trực tiếp API Key vào thanh **"Cấu Hình Google Gemini API"** ngay trên giao diện web `http://localhost:8080`, bấm **"Test Key"** để kiểm tra và lưu tự động vào trình duyệt.
   - **Cách 2 (Thiết lập biến môi trường)**:
     ```powershell
     $env:GEMINI_API_KEY="AIzaSyYourActualKeyHere"
     python app.py
     ```

---

## 📁 3. Cấu Trúc Mã Nguồn

```
c:\Users\admin\Downloads\AI Agent\
├── app.py                     # Web Server cục bộ & Điều phối Agent REST API
├── gemini_service.py          # Module kết nối và gọi Google Gemini API
├── agent_engine.py            # Logic cốt lõi của các Node trong sơ đồ + Gemini Hook
├── test_pipeline.py           # Script kiểm thử tự động toàn bộ quy trình
├── .env.example               # Mẫu file cấu hình API Key và Model
├── README.md                  # Hướng dẫn chi tiết sử dụng & tài liệu hệ thống
├── templates/
│   └── index.html             # Giao diện Web tương tác (Tailwind + Chart.js)
├── sample_data/
│   └── doanh_thu_ban_le_sample.csv # Dữ liệu bán lẻ thực tế (có lỗi để test cleaning)
├── prompts/
│   └── system_prompts.py      # Hệ thống Prompt chuyên nghiệp cho từng Sub-Agent
└── reports/                   # Thư mục lưu trữ Dashboard HTML và file dữ liệu sạch
```

---

## 🚀 4. Hướng Dẫn Vận Hành

### Bước 1: Khởi động Server
```powershell
cd "c:\Users\admin\Downloads\AI Agent"
python app.py
```

### Bước 2: Truy cập Giao diện Web
Mở trình duyệt (Chrome, Edge...) và truy cập:
👉 **`http://localhost:8080`**

### Bước 3: Trải nghiệm Phân tích
1. Dán **Gemini API Key** và bấm **"Test Key"** (hoặc để trống để dùng Local Engine).
2. Tùy ý điền **Bối cảnh doanh nghiệp** (Tên công ty, Ngành hàng, Mục tiêu, Câu hỏi kinh doanh).
3. Chọn nguồn dữ liệu (Upload Excel/CSV, dán link Google Sheet, hoặc tab "Dùng Dữ Liệu Mẫu").
4. Bấm **"BẮT ĐẦU CHẠY QUY TRÌNH PHÂN TÍCH"**.
5. Thử nghiệm tính năng **Feedback** để Gemini điều chỉnh góc nhìn phân tích, hoặc bấm **"Xác Nhận & Xuất Báo Cáo"** để nhận Dashboard HTML tương tác.
