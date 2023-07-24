# AIquizgenerator
 Ứng dụng tạo câu trắc nghiệm do OpenAI tổng hợp

Tính năng:
- Gọi OpenAI api để dựa vào đầu vào là thông tin chỉ định sẵn tạo ra câu trắc nghiệm.

Yêu cầu trước khi cài đặt:
- Có sẵn api của OpenAI còn token để sử dụng, có dạng "k-xWbuyrYy621Ud9jo4DK4T3BlbkFJI8qhTcopusH9b6M.....". Các lấy mã api của OpenAI thì Google nhe.
- Cài đặt các gói thư viện của Python. Mở cmd bằng quyền admin, chạy tuần tự các câu lệnh bên dưới
    pip install Flask
    pip install openai
    pip install requests
    pip install sqlite3
    pip install datetime
- Các công cụ hỗ trợ: Visual Studio Code, DB Browser for SQLite (dùng đọc database của sqlite)

Các bước cài đặt:
- Vào đường dẫn https://github.com/hhoanganh/AIquizgenerator chọn vào nút có chữ Code màu xanh bên góc phải, chọn Download ZIP
- Giải nén folder vừa tải xuống
- Mở file app.py bằng Visual Studio Code hoặc Notepad++, sửa các đoạn code bên dưới:
    1. app = Flask(__name__, static_folder='C:/aigenquiz - 2307/static') -> sửa đoạn 'C:/aigenquiz - 2307/static' bằng đường dẫn mới. Ví dụ giải nén file ZIP vào ổ C, đặt tên là 'AIquizgenerator-main' thì đường dẫn mới là 'C:/AIquizgenerator-main/static'
    2. api_key = "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" -> chép vào đoạn mã api của OpenAI mới, thay cho đoạn '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'. Đoạn này cũ hết token rồi. Khi gọi tới sẽ báo lỗi.

Chạy ứng dụng:
- Mở cmd bằng quyền admin, di chuyển tới folder của ứng dụng. Ví dụ giải nén file ZIP vào ổ C, đặt tên là 'AIquizgenerator-main' thì chạy 'cd c:\AIquizgenerator-main'. 
- Chạy tiếp câu lệnh 'python app.py'. Lúc này màn hình cmd thể hiện 2 đường dẫn gồm IP kèm port 5000 (2 đường dẫn một cái là localhost dạng 'http://127.0.0.1:5000' và một cái là IP của máy đang chạy dạng 'http://IP của máy:5000'). Truy cập vào 1 trong 2 đường dẫn này để chạy ứng dụng. Ví dụ mở web truy cập 'http://127.0.0.1:5000'.
- Trên màn hình thể hiện trang chính của ứng dụng.
- Để truy cập ứng dụng từ máy khác hoặc điện thoại, sử dụng đường dẫn 'http://IP của máy :5000', chú ý máy này phải cùng lớp mạng hoặc ping được đến IP của máy chủ đang chạy ứng dụng.