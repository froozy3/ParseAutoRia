import asyncio
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import settings
from database import dump_database, init_db
from scraper import main_scrape

# Initialize logger
logger = logging.getLogger(__name__)


async def perform_dump():
    """Perform database dump."""
    logger.info("Starting database dump")
    try:
        await dump_database()
        logger.info("Database dump completed successfully")
    except Exception as e:
        logger.error(f"Error during database dump: {str(e)}", exc_info=True)


async def schedule_scraping():
    """Perform daily scraping and database dump."""
    logger.info("Starting scheduled scraping")

    try:
        # Execute main scraping
        await main_scrape()

        # Perform database dump if scheduled
        if (
            settings.SCRAPE_HOUR == settings.DUMP_HOUR
            and settings.SCRAPE_MINUTE == settings.DUMP_MINUTE
        ):
            await dump_database()
            logger.info("Database dump completed successfully")

    except Exception as e:
        logger.error(f"Error during scheduled scraping: {str(e)}", exc_info=True)
        raise


async def main():
    """Initialize the database and run the scheduler."""
    try:
        # Create dumps directory if it doesn't exist
        os.makedirs("dumps", exist_ok=True)

        # Initialize the database connection
        await init_db()
        logger.info("Database initialized successfully")

        # Create an AsyncIO scheduler with timezone
        scheduler = AsyncIOScheduler(timezone="Europe/Kiev")

        # Add a scraping job to the scheduler
        scheduler.add_job(
            schedule_scraping,
            CronTrigger(hour=settings.SCRAPE_HOUR, minute=settings.SCRAPE_MINUTE),
            name="scraping_job",
            replace_existing=True,
            misfire_grace_time=None,  # Allow job to run even if missed
        )

        scheduler.add_job(
            perform_dump,
            CronTrigger(hour=settings.DUMP_HOUR, minute=settings.DUMP_MINUTE),
            name="dump_job",
            replace_existing=True,
            misfire_grace_time=None,  # Allow job to run even if missed
        )

        # Start the scheduler
        scheduler.start()
        logger.info(
            f"Scheduled scraping job for {settings.SCRAPE_HOUR}:{settings.SCRAPE_MINUTE}"
        )
        logger.info("Scheduler started successfully")

        # Keep the script running indefinitely
        while True:
            await asyncio.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("scraper.log"),
            logging.StreamHandler(),
        ],
    )

    # Run the main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
