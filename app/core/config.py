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
    
    # 源数据库配置
    SOURCE_DB_HOST: str
    SOURCE_DB_PORT: str
    SOURCE_DB_USER: str
    SOURCE_DB_PASSWORD: str
    SOURCE_DB_NAME: str

    @property
    def SOURCE_DB_URL(self) -> str:
        return f"mysql+pymysql://{self.SOURCE_DB_USER}:{self.SOURCE_DB_PASSWORD}@{self.SOURCE_DB_HOST}:{self.SOURCE_DB_PORT}/{self.SOURCE_DB_NAME}"

    # 目标数据库配置
    TARGET_DB_HOST: str
    TARGET_DB_PORT: str
    TARGET_DB_USER: str
    TARGET_DB_PASSWORD: str
    TARGET_DB_NAME: str

    @property
    def TARGET_DB_URL(self) -> str:
        return f"mysql+pymysql://{self.TARGET_DB_USER}:{self.TARGET_DB_PASSWORD}@{self.TARGET_DB_HOST}:{self.TARGET_DB_PORT}/{self.TARGET_DB_NAME}"

    # 结果存储数据库配置
    RESULT_DB_HOST: str
    RESULT_DB_PORT: str
    RESULT_DB_USER: str
    RESULT_DB_PASSWORD: str
    RESULT_DB_NAME: str

    @property
    def RESULT_DB_URL(self) -> str:
        return f"mysql+pymysql://{self.RESULT_DB_USER}:{self.RESULT_DB_PASSWORD}@{self.RESULT_DB_HOST}:{self.RESULT_DB_PORT}/{self.RESULT_DB_NAME}"

    # 企业微信配置
    WECHAT_WEBHOOK_KEY: Optional[str] = Field(default=None)
    WECHAT_ALERT_ENABLED: bool = Field(default=False)

    # 定时任务配置
    SCHEDULER_ENABLED: bool = Field(default=True)
    DEFAULT_COMPARISON_CRON: str = Field(default="0 0 * * *")

    # 报告配置
    REPORT_OUTPUT_DIR: str = Field(default="./reports")
    PDF_ENABLED: bool = Field(default=True)
    HTML_ENABLED: bool = Field(default=True)


settings = Settings() 