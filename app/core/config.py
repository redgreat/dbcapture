import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    APP_NAME: str = Field(default="DBCapture")
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    API_PREFIX: str = Field(default="/api/v1")
    SECRET_KEY: str
    
    # 数据库配置
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @property
    def DB_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 企业微信配置
    WECHAT_WEBHOOK_KEY: Optional[str] = Field(default=None)
    WECHAT_ALERT_ENABLED: bool = Field(default=False)

    # 报告配置
    REPORT_OUTPUT_DIR: str = Field(default="./reports")


settings = Settings()
