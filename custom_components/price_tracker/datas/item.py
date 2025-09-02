import dataclasses
from typing import Optional, Any, List
from enum import Enum

from custom_components.price_tracker.datas.category import ItemCategoryData
from custom_components.price_tracker.datas.delivery import DeliveryData
from custom_components.price_tracker.datas.inventory import InventoryStatus
from custom_components.price_tracker.datas.price import ItemPriceData
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType


@dataclasses.dataclass
class ItemOptionData:
    def __init__(self, id: Any, name: str, price: float, inventory: Optional[int] = 0):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = inventory if inventory is not None else 0
        self.inventory_status = InventoryStatus.of(is_sold_out=False, stock=self.quantity)

    @property
    def dict(self):
        return {
            "option_id": self.id,
            "name": self.name,
            "price": self.price,
            "inventory_status": self.inventory_status.name,
            "quantity": self.quantity,
        }


class ItemStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"


@dataclasses.dataclass
class ItemData:
    id: Any
    name: str = "UNKNOWN"
    price: ItemPriceData = dataclasses.field(default_factory=ItemPriceData)
    brand: Optional[str] = None
    description: Optional[str] = None
    category: ItemCategoryData = dataclasses.field(default_factory=ItemCategoryData)
    delivery: DeliveryData = dataclasses.field(default_factory=DeliveryData)
    url: Optional[str] = None
    image: Optional[str] = None
    unit: ItemUnitData = dataclasses.field(default_factory=lambda: ItemUnitData(unit=1, price=0, unit_type=ItemUnitType.PIECE))
    inventory: InventoryStatus = InventoryStatus.OUT_OF_STOCK
    options: Optional[List[ItemOptionData]] = dataclasses.field(default_factory=list)
    status: ItemStatus = ItemStatus.ACTIVE
    http_status: int = 200

    @property
    def total_price(self):
        return self.price

    @property
    def dict(self):
        data = {
            "product_id": self.id,
            "brand": self.brand,
            "name": self.name,
            "description": self.description,
            "display_category": self.category.split
            if self.category is not None
            else None,
            "display_category_last": self.category.last
            if self.category is not None
            else None,
            "original_price": self.price.original_price,
            "price": self.price.price,
            "discount_rate": self.price.discount_rate,
            "discount_amount": self.price.discount_amount,
            "payback_price": self.price.payback_price,
            "currency": self.price.currency,
            "delivery_type": self.delivery.delivery_type.name,
            "delivery_pay_type": self.delivery.pay_type.name,
            "delivery_price": self.delivery.price,
            "delivery_free_threshold_price": self.delivery.threshold_price,
            "delivery_minimum_price": self.delivery.minimum_price,
            "delivery_arrive_date": self.delivery.arrive_date,
            "url": self.url,
            "image": self.image,
            "inventory_status": self.inventory.name,
            "inventory_status_rank": self.inventory.rank,
            "unit_value": self.unit.unit,
            "unit_type": self.unit.unit_type.name,
            "unit_price": self.unit.price,
            "sort_price": "{}:{}".format(
                str(self.price.price).ljust(12, "0"), self.inventory.lower_rank
            ),
            "product_options": [option.dict for option in self.options]
            if self.options is not None
            else [],
            "status": self.status.name
            if self.status is not None
            else ItemStatus.ACTIVE.name,
            "http_status": self.http_status,
        }

        # For fast-access options
        if self.options is not None:
            for idx, option in enumerate(self.options):
                data[f"product_option_{idx}_id"] = option.id
                data[f"product_option_{idx}_name"] = option.name
                data[f"product_option_{idx}_price"] = option.price
                data[f"product_option_{idx}_quantity"] = option.quantity

        return data

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["product_id"],
            name=data["name"],
            brand=data["brand"],
            product_link=data["product_link"],
            status=ItemStatus[data["status"]],
            price=ItemPriceData(
                price=data["price"],
                original_price=data.get("original_price", 0.0),
                discount_rate=data.get("discount_rate", 0.0),
                discount_amount=data.get("discount_amount", 0.0),
                payback_price=data.get("payback_price", 0.0),
                currency=data.get("currency", "UNKNOWN"),
            ),
            url=data["url"],
            image=data["image"],
            inventory=InventoryStatus[data["inventory_status"]],
            unit=ItemUnitData(
                unit=data.get("unit_value", 1),
                unit_type=ItemUnitType[data.get("unit_type", "PIECE")],
                price=data.get("unit_price", 0.0),
            ),
            category=ItemCategoryData(
                categories=data.get("display_category", []),
            ),
            delivery=DeliveryData(
                delivery_type=data.get("delivery_type", "UNKNOWN"),
                pay_type=data.get("delivery_pay_type", "UNKNOWN"),
                price=data.get("delivery_price", 0.0),
                threshold_price=data.get("delivery_free_threshold_price", 0.0),
                minimum_price=data.get("delivery_minimum_price", 0.0),
                arrive_date=data.get("delivery_arrive_date"),
            ),
            options=[ItemOptionData(**opt) for opt in data.get("product_options", [])],
            http_status=data.get("http_status"),
        )
