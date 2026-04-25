from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "AI Agent - Student Performance Analytics"
    app_env: str = "dev"
    session_secret_key: str = "change-me-in-env"

    teacher_avatar: str = "👤"
    teacher_default_password: str = "123456"
    teacher_accounts: dict[str, str] = Field(
        default_factory=lambda: {
            "ntnhu@ttn.edu.vn": "ThS. Nguyễn Thị Như",
            "htphuong@ttn.edu.vn": "TS. Hồ Thị Phượng",
            "tthgiang@ttn.edu.vn": "TS. Trương Thị Hương Giang",
            "phamvanthuan@ttn.edu.vn": "ThS. Phạm Văn Thuận",
            "nqcuong@ttn.edu.vn": "NCS. Nguyễn Quốc Cường",
            "txthang@ttn.edu.vn": "NCS. Trần Xuân Thắng",
            "tungocthao@ttn.edu.vn": "NCS. Từ Ngọc Thảo",
            "truonghai@ttn.edu.vn": "ThS. Trương Hải",
            "ndthang@ttn.edu.vn": "ThS. Nguyễn Đức Thắng",
            "ptdtrang@ttn.edu.vn": "ThS. Phan Thị Đài Trang",
            "pxtho@ttn.edu.vn": "ThS. Phan Xuân Thọ",
            "hqdu@ttn.edu.vn": "CN. Hoàng Quang Du",
        }
    )

    sqlserver_host: str = "localhost"
    sqlserver_port: int = 1433
    sqlserver_database: str = "StudentAnalytics"
    sqlserver_user: str = "sa"
    sqlserver_password: str = "YourStrong!Passw0rd"
    sqlserver_driver: str = "ODBC Driver 17 for SQL Server"
    sqlserver_trusted_connection: bool = False
    sqlserver_encrypt: str = "no"
    sqlserver_trust_server_certificate: str = "yes"

    xai_api_key: str = ""
    xai_model: str = "grok-3-mini"
    xai_base_url: str = "https://api.x.ai/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
