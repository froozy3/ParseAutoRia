from asyncio.log import logger
import random
import re
from typing import List


def parse_odometer(odometer_str: str) -> int:
    """Convert odometer string to integer."""
    if not odometer_str:
        return 0

    # Extract numbers and multiplier (тыс., км)
    match = re.search(r"(\d+(?:\s*\d+)?)\s*(тис\.?|тыс\.?|км)?", odometer_str.lower())

    if not match:
        return 0

    value = int(match.group(1))
    multiplier = match.group(2)

    if multiplier and "тис" in multiplier:
        value *= 1000

    return value


def parse_price(price_text: str) -> int:
    """
    Parse price string into USD value.
    Handles formats:
    - "24 200 €" -> 26620 (EUR conversion)
    - "6 999 $" -> 6999 (USD)
    - "300 000 грн" -> 7281 (UAH conversion)
    """
    if not price_text or price_text == "0":
        return 0

    # Clean the price text
    clean_price = price_text.strip().replace(" ", "")

    # Extract number using regex
    number_match = re.search(r"(\d+)", clean_price)
    if not number_match:
        return 0

    try:
        amount = int(number_match.group(1))

        # Convert based on currency
        if "€" in clean_price:
            return int(amount * 1.1)  # EUR to USD
        elif "грн" in clean_price:
            return int(amount / 41.22)  # UAH to USD
        else:
            return amount  # Assume USD

    except (ValueError, TypeError):
        return 0


def parse_phone(phone_str: str) -> str:
    """Normalize phone number format."""
    if not phone_str:
        return ""

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone_str)

    # Format as +380XXXXXXXXX
    if digits.startswith("380") and len(digits) == 11:
        return f"+{digits}"
    elif digits.startswith("80") and len(digits) == 10:
        return f"+3{digits}"
    elif digits.startswith("0") and len(digits) == 9:
        return f"+38{digits}"
    else:
        return f"+380{digits[-9:]}" if digits else ""
