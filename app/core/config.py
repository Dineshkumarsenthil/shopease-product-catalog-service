from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """All values come from environment variables or the .env file."""

    # Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_root_password: str
    mysql_database: str = "shopease_product_catalog_db"

    # JWT (must match the Authentication Service)
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_user_id_claim: str = "sub"
    jwt_role_claim: str = "role"
    admin_role: str = "admin"

    # Inventory
    low_stock_threshold: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> URL:
        # URL.create handles special characters in the password for us
        return URL.create(
            drivername="mysql+pymysql",
            username="root",
            password=self.mysql_root_password,
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
        )


settings = Settings()
