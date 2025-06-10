import asyncio
from datetime import datetime
import json
import logging
import os
import random
from typing import Dict, List, Optional
from aiohttp import TCPConnector

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from sqlalchemy import select
from database import car_exists, get_db, init_db, save_cars
from config import settings
from models import Car
from utils import parse_odometer, parse_phone, parse_price

logger = logging.getLogger(__name__)


def setup_logging():
    """Setup logging to file and console."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("scraper.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


class AutoRiaScraper:
    def __init__(self, session: ClientSession):
        self.session = session
        self.headers = {
            "User-Agent": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/89.0",
            ]
        }

    async def fetch(self, url: str) -> Optional[str]:
        """Enhanced fetch with retries and rotating user agents"""
        for attempt in range(settings.RETRY_ATTEMPTS):
            headers = {"User-Agent": random.choice(self.headers["User-Agent"])}
            try:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                async with self.session.get(
                    url, headers=headers, timeout=settings.REQUEST_TIMEOUT
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Rate limit
                        await asyncio.sleep(5 * (attempt + 1))
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
        return None

    async def extract_car_links(self, html: str) -> List[str]:
        """Extract car links from the HTML content of the page."""
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("section.ticket-item a.address")
        return [card.get("href") for card in cards if card.get("href")]

    async def get_car_links(self, page: int = 1) -> List[str]:
        """Get car links from the specified page."""
        url = f"{settings.START_URL}?page={page}"
        html = await self.fetch(url)
        return await self.extract_car_links(html) if html else []

    async def parse_car_page(self, url: str) -> Car | None:
        """Parse a single car page and return Car object."""

        if "newauto" in url:
            logger.debug(f"Skipping new car page: {url}")
            return None

        if await car_exists(url):
            logger.debug(f"Skipping already processed car: {url}")
            return None

        html = await self.fetch(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")

        try:
            # Get all elements in one pass to minimize DOM access
            elements = {
                "title": soup.select_one("h1.head"),
                "price": soup.select_one("div.price_value strong"),
                "odometer": soup.select_one("div.base-information.bold"),
                "username": soup.select_one("div.seller_info_name.bold"),
                "vin": soup.select_one("span.label-vin"),
                "car_number": soup.select_one("span.state-num.ua"),
                "phones": soup.select("div.phones_item span.phone.bold"),
                "images": soup.select("div.photo-620x465 picture source"),
            }

            phones = []
            for phone_elem in elements["phones"]:
                try:
                    phone = parse_phone(phone_elem.get_text(strip=True))
                    if phone:
                        phones.append(phone)
                except Exception as e:
                    continue

            # Process image data
            image_url = None
            images_count = 0
            if elements["images"]:
                try:
                    first_image = elements["images"][0]
                    image_url = (
                        first_image.get("srcset")
                        or first_image.get("src")
                        or first_image.get("data-src")
                    )
                    images_count = len(elements["images"])
                except (IndexError, AttributeError):
                    pass

            # Create Car object with direct element access
            return Car(
                url=url,
                title=elements["title"].get_text(strip=True),
                price_usd=parse_price(
                    elements["price"].get_text(strip=True) if elements["price"] else "0"
                ),
                odometer=parse_odometer(
                    elements["odometer"].get_text(strip=True)
                    if elements["odometer"]
                    else "0"
                ),
                username=elements["username"].get_text(strip=True)
                if elements["username"]
                else "Unknown",
                phone_number=phones[0] if phones else "",
                image_url=image_url,
                images_count=images_count,
                car_vin=elements["vin"].get_text(strip=True) if elements["vin"] else "",
                car_number=elements["car_number"].contents[0]
                if elements["car_number"] and elements["car_number"].contents
                else "",
                datetime_found=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error parsing car page {url}: {e}", exc_info=True)
            return None


async def save_to_json(cars: List[Car], filename: str = None) -> str:
    """Save cars to JSON file with timestamp"""
    if not filename:
        filename = f"dumps/cars_dump_{datetime.now():%Y%m%d_%H%M%S}.json"

    os.makedirs("dumps", exist_ok=True)

    # Convert cars to dictionaries
    cars_data = [
        {
            "url": car.url,
            "title": car.title,
            "price_usd": car.price_usd,
            "odometer": car.odometer,
            "username": car.username,
            "phone_number": car.phone_number,
            "image_url": car.image_url,
            "images_count": car.images_count,
            "car_vin": car.car_vin,
            "car_number": car.car_number,
            "datetime_found": car.datetime_found.isoformat(),
        }
        for car in cars
    ]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cars_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(cars)} cars to {filename}")
    return filename


async def bulk_check_existence(urls: List[str]) -> Dict[str, bool]:
    """Check if multiple car URLs exist in the database."""
    try:
        async with get_db() as session:
            # Query to check existence of multiple URLs
            result = await session.execute(select(Car.url).where(Car.url.in_(urls)))
            existing_urls = {row[0] for row in result.fetchall()}

        # Return a dictionary with URL existence status
        return {url: url in existing_urls for url in urls}

    except Exception as e:
        logger.error(f"Error in bulk_check_existence: {str(e)}")
        return {url: False for url in urls}


async def scrape_all_pages() -> List[Car]:
    """Scrape all pages and return a list of cars."""
    cars_list = []

    async with ClientSession(
        connector=TCPConnector(limit=settings.MAX_CONCURRENT_REQUESTS)
    ) as session:
        scraper = AutoRiaScraper(session)

        # Define process_page function
        async def process_page(page: int) -> List[Car]:
            car_links = await scraper.get_car_links(page)
            if not car_links:
                return []

            # Filter out already existing cars in bulk
            existence_results = await bulk_check_existence(car_links)
            new_car_links = [
                url for url, exists in existence_results.items() if not exists
            ]

            # Process new cars
            tasks = [scraper.parse_car_page(link) for link in new_car_links]
            cars = await asyncio.gather(*tasks)
            return [car for car in cars if car]

        # Collect and process pages in parallel
        tasks = [
            process_page(page)
            for page in range(
                settings.START_PAGE, settings.START_PAGE + settings.MAX_PAGES
            )
        ]
        results = await asyncio.gather(*tasks)

        # Flatten the list of cars
        for cars in results:
            cars_list.extend(cars)

    return cars_list


async def main_scrape():
    """Main function to run the scraper with JSON dump and DB save."""
    start_time = datetime.now()
    logger.info("Starting the AutoRia scraper...")

    cars_list = await scrape_all_pages()

    # Save to JSON if enabled
    if settings.SAVE_TO_JSON and cars_list:
        json_file = await save_to_json(cars_list)
        logger.info(f"JSON dump created: {json_file}")

    # Save to database in batches
    if settings.SAVE_TO_DB and cars_list:
        await save_cars(cars_list)
        logger.info(f"Saved {len(cars_list)} cars to the database.")

    duration = datetime.now() - start_time
    logger.info(
        f"Scraping completed in {duration}. " f"Total cars collected: {len(cars_list)}"
    )


# if __name__ == "__main__":
#     # Setup logging
#     setup_logging()

#     # Create dumps directory if it doesn't exist
#     os.makedirs("dumps", exist_ok=True)

#     # Run the scraper
#     async def run():
#         await init_db()  # Initialize database
#         await main_scrape()

#     asyncio.run(run())
