import logging
from abc import abstractmethod

from custom_components.price_tracker.datas.item import ItemData
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


class PriceEngine:
    item_url: str
    id: any

    @abstractmethod
    async def load(self) -> ItemData | None:
        """Load item data from source."""
        raise NotImplementedError()

    @abstractmethod
    def id_str(self) -> str:
        """Return string id for engine."""
        raise NotImplementedError()

    @property
    def device_id(self) -> str | None:
        """Return device id if available."""
        return None

    @property
    def entity_id(self) -> str:
        """Return entity id for engine."""
        import logging
        logger = logging.getLogger(__name__)
        value = self.id
        # If value is dict, prefer both product_id and item_url
        if isinstance(value, dict):
            product_id = value.get("product_id")
            item_url = value.get("item_url")
            if product_id and item_url:
                logger.info(f"[DIAG][PriceEngine.entity_id] Using product_id and item_url for entity_id: {product_id}, {item_url}")
                return self.target_id({"product_id": product_id, "item_url": item_url})
            elif product_id:
                logger.info(f"[DIAG][PriceEngine.entity_id] Using product_id only for entity_id: {product_id}")
                return self.target_id({"product_id": product_id})
            else:
                logger.error(f"[DIAG][PriceEngine.entity_id] No valid product_id in value: {value}")
                return "invalid_product_id"
        logger.info(f"[DIAG][PriceEngine.entity_id] Using value for entity_id: {value}")
        return self.target_id(value)

    @staticmethod
    def target_id(value: any) -> str:
        """Generate target id for entity/device."""
        if isinstance(value, dict):
            product_id = value.get("product_id")
            if product_id:
                return product_id
            # If no product_id, join all non-None values
            items = [v for k, v in value.items() if v is not None]
            if items:
                return "_".join(items)
            return "invalid_product_id"
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            items = Lu.filter(value, lambda x: x is not None)
            return "_".join(items) if items else "invalid_product_id"
        return str(value)

    @staticmethod
    def parse_id(item_url: str) -> any:
        """Parse ID from URL."""
        raise NotImplementedError()

    @staticmethod
    def engine_code() -> str:
        """Return engine code."""
        raise NotImplementedError()

    @staticmethod
    def engine_name() -> str:
        """Return engine readable name."""
        raise NotImplementedError()
