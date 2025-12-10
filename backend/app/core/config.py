from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_DRIVER: str = "mysql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "sanjaya"
    DB_USER: str = "sanjaya"
    DB_PASSWORD: str = "password"

    class Config:
        env_file = ".env"


settings = Settings()

