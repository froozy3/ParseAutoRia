from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    price_usd: Mapped[int] = mapped_column(Integer)
    odometer: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    images_count: Mapped[int] = mapped_column(Integer)
    car_vin: Mapped[str] = mapped_column(String)
    car_number: Mapped[str] = mapped_column(String)
    datetime_found: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Car {self.title}>"
    
