# AI Agent Web App - Phan tich ket qua hoc tap sinh vien

Ung dung web su dung Python, SQL Server va Grok API de:
- Phan tich diem so va lich su hoc tap
- Danh gia xu huong tien bo/sa sut
- Phat hien sinh vien nguy co hoc yeu hoac rot mon
- Goi y ke hoach hoc tap ca nhan hoa

## 1) Cau truc du an

```text
Do_an/
  app/
    api/routes.py
    core/config.py
    core/database.py
    models/student.py
    repositories/student_repository.py
    schemas/report.py
    services/analytics_service.py
    services/ai_report_service.py
    static/style.css
    templates/index.html
    main.py
  scripts/init_db.sql
  .env.example
  requirements.txt
  README.md
```

## 2) Cai dat

1. Tao moi truong ao
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.venv\\Scripts\\Activate.ps1`
2. Cai thu vien
   - `pip install -r requirements.txt`
3. Tao file `.env` tu `.env.example` va dien thong tin SQL Server + XAI_API_KEY.

## 2.1) De nguoi khac clone ve chay y het

1. Day len git cac file code + `requirements.txt` + `.env.example`.
2. KHONG day file `.env` va thu muc `.venv`.
3. Ben may moi, clone project, tao `.env` tu `.env.example`, dien dung thong tin SQL Server va API key.
4. Cai dung Python version (khuyen nghi 3.11.x).
5. Chay dung lenh khoi dong trong muc 4 de server reload khi save code.

Checklist nhanh truoc khi gui cho nguoi khac:
- `requirements.txt` day du thu vien
- `.env.example` khong chua secret that
- SQL Server da tao DB `StudentAnalytics`
- Chay duoc `/health` tra ve `{ "status": "ok" }`

## 3) Khoi tao CSDL SQL Server

- Mo SQL Server Management Studio va chay file `scripts/init_db.sql`.
- Script se tao database `StudentAnalytics`, bang du lieu va seed mau.

## 4) Chay ung dung

- Lenh chay:
  - Windows PowerShell:
    - `D:\Home\JOB\Do_an\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload`
- Truy cap:
  - `http://127.0.0.1:8010`

## 5) Cach dung

- Nhap ma so sinh vien hoac ho ten.
- Bam **Tao Bao Cao AI**.
- He thong tra ve:
  - Tong quan ket qua hoc tap
  - Muc do rui ro (LOW/MEDIUM/HIGH)
  - Goi y cai thien
  - Bao cao chi tiet do Grok tao

## 6) Ghi chu ky thuat

- Endpoint API: `POST /api/v1/report`
- Neu chua co `XAI_API_KEY`, he thong van phan tich noi bo va tra thong bao cau hinh API.
- Co the mo rong them:
  - Dashboard theo lop/khoa
  - Phan quyen giao vien/co van
  - Lich su canh bao theo thang
