from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int

    model_config = SettingsConfigDict(env_file=".env", from_attributes=True)


settings = Settings()  # type: ignore
