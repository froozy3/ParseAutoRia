from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    POSTGRES_DB: str  # Name of the PostgreSQL database
    POSTGRES_USER: str  # Username for the PostgreSQL database
    POSTGRES_PASSWORD: str  # Password for the PostgreSQL database
    DB_HOST: str = "localhost"  # Host address of the database (default: localhost)
    DB_PORT: str = "5432"  # Port for the database connection (default: 5432)
    DATABASE_URL: str | None = None  # Full database connection URL (optional)

    # Scraper settings
    START_URL: str = "https://auto.ria.com/uk/car/used/"  # Starting URL for scraping
    START_PAGE: int = 1  # Starting page number for scraping
    MAX_PAGES: int | None = 7  # Maximum number of pages to scrape (None for unlimited)

    # Scheduler settings
    SCRAPE_HOUR: int  # Hour of the day to run the scraping job
    SCRAPE_MINUTE: int  # Minute of the hour to run the scraping job
    # Dump settings
    DUMP_HOUR: int  # Hour of the day to perform the database dump
    DUMP_MINUTE: int  # Minute of the hour to perform the database dump
    DUMPS_DIR: str = "dumps"  # Directory to save database dumps

    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = 20  # Maximum number of concurrent requests
    RETRY_ATTEMPTS: int = 2  # Number of retry attempts for failed requests
    REQUEST_TIMEOUT: int = 10  # Timeout for HTTP requests in seconds

    # JSON settings
    SAVE_TO_JSON: bool = True  # Whether to save scraped data to JSON
    JSON_INDENT: int = 2  # Indentation level for JSON formatting
    SAVE_TO_DB: bool = True  # Whether to save scraped data to the database

    # Application settings
    LOG_LEVEL: str = "INFO"  # Logging level (e.g., DEBUG, INFO, WARNING, ERROR)
    LOCAL_LAUNCH: bool = True  # Whether the application is running locally

    class Config:
        env_file = ".env"  # Path to the environment variables file
        env_file_encoding = "utf-8"  # Encoding for the environment variables file
        case_sensitive = True  # Ensure environment variable names are case-sensitive

    def __init__(self, **kwargs):
        """Initialize settings and construct the DATABASE_URL if not provided."""
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
            )


# Create a global settings instance
settings = Settings(SCRAPE_HOUR=18, SCRAPE_MINUTE=44, DUMP_HOUR=18, DUMP_MINUTE=45)
