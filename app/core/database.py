from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import URL

from app.core.config import settings


def build_connection_url() -> str:
    query = {
        "driver": settings.sqlserver_driver,
        "Encrypt": settings.sqlserver_encrypt,
        "TrustServerCertificate": settings.sqlserver_trust_server_certificate,
    }

    if settings.sqlserver_trusted_connection:
        query["trusted_connection"] = "yes"
        return str(
            URL.create(
                "mssql+pyodbc",
                host=settings.sqlserver_host,
                port=settings.sqlserver_port,
                database=settings.sqlserver_database,
                query=query,
            )
        )

    return str(
        URL.create(
            "mssql+pyodbc",
            username=settings.sqlserver_user,
            password=settings.sqlserver_password,
            host=settings.sqlserver_host,
            port=settings.sqlserver_port,
            database=settings.sqlserver_database,
            query=query,
        )
    )


engine = create_engine(build_connection_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
