from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base project .env settings"""
    db_host: str
    db_port: int
    db_name: str
    db_pass: str
    db_user: str

    bot_token: str
    admin_id: int

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}?async_fallback=True"

    @property
    def  DATABASE_URL_sync(self):
        return f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
