# AutoRIA Scraper

An asynchronous web scraper for AutoRIA built with Python. Collects car listings data and stores it in PostgreSQL database.

## Features

- Asynchronous web scraping using `aiohttp`
- PostgreSQL database storage with `asyncpg`
- Scheduled scraping with `APScheduler`
- Configurable through environment variables
- JSON data export
- Database dumps

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ParseAutoRia
```

2. Create `.env` file:
```properties
# Database settings
POSTGRES_DB=autoria
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Scheduler settings
SCRAPE_HOUR=12
SCRAPE_MINUTE=00
DUMP_HOUR=12
DUMP_MINUTE=30
START_URL=https://auto.ria.com/uk/car/used/

# Performance tuning
MAX_CONCURRENT_REQUESTS=10
RETRY_ATTEMPTS=3
REQUEST_TIMEOUT=10

# Application settings
LOG_LEVEL=INFO
LOCAL_LAUNCH=True
```

### Local Setup

1. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install PostgreSQL and create database

4. Create required directories:
```bash
mkdir dumps
```

5. Configure environment variables in `.env`

6. Run the scheduler or just script:
    SCHEDULER:
    ```bash
    python scheduler.py
    ```
    SCRIPT 
    ```bash
    python scraper.py
    ```

## Project Structure

```
ParseAutoRia/
├── requirements.txt
├── .env
├── .gitignore
├── scraper.py      # Main scraping logic
├── scheduler.py    # Scheduling functionality
├── config.py       # Configuration settings
├── database.py     # Database operations
├── dumps/          # Data dumps directory
└── scraper.log/          # Log files directory
```

## Configuration

Configure the scraper through environment variables in `.env`:

- `SCRAPE_HOUR`, `SCRAPE_MINUTE`: Schedule scraping time
- `DUMP_HOUR`, `DUMP_MINUTE`: Schedule database dumps
- `MAX_CONCURRENT_REQUESTS`: Concurrent request limit
- `MAX_PAGES`: Number of pages to scrape
- `SAVE_TO_JSON`: Enable JSON export
- `SAVE_TO_DB`: Enable database storage

