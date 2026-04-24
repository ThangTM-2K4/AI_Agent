from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Agent - Student Performance Analytics"
    app_env: str = "dev"

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
