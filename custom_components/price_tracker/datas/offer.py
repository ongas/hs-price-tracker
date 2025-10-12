import dataclasses
from typing import Optional


@dataclasses.dataclass
class ItemOfferData:
    def __init__(
        self,
        seller: str,
        price: float,
        url: Optional[str] = None,
        currency: Optional[str] = None,
    ):
        self.seller = seller
        self.price = price
        self.url = url
        self.currency = currency

    @property
    def dict(self):
        return {
            "seller": self.seller,
            "price": self.price,
            "url": self.url,
            "currency": self.currency,
        }
