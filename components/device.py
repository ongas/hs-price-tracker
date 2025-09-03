from abc import abstractmethod
from datetime import datetime
from typing import Optional, List, Union
from homeassistant.helpers.entity import Entity

from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.defaults import DOMAIN, VERSION

_HAS_DEVICEINFO = False
try:
    from homeassistant.helpers.device_registry import DeviceInfo
    _HAS_DEVICEINFO = True
except ImportError:
    DeviceInfo = None


class PriceTrackerDevice(Entity):
    _name: Optional[str]
    _proxies: List[str]

    def __init__(
        self,
        entry_id: str,
        device_type: str,
        device_id: str,
        proxies: Optional[Union[str, List[str]]] = None,
    ):
        self._entry_id: str = entry_id
        self._device_id: str = str(device_id)
        self._device_type: str = device_type
        self._generate_device_id: str = IdGenerator.generate_device_id(
            self._device_id
        )
        self._attr_available: bool = True
        self._updated_at: Optional[datetime] = None
        self._name: Optional[str] = None
        if isinstance(proxies, str):
            self._proxies = [proxies]
        elif isinstance(proxies, list):
            self._proxies = proxies
        else:
            self._proxies = []
        self.entity_id: str = self._generate_device_id

    @property
    def proxies(self) -> List[str]:
        return self._proxies

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def unique_id(self) -> str:
        return self.entity_id

    @property
    def name(self) -> str:
        return self._name if self._name is not None else self._device_id

    if _HAS_DEVICEINFO:
        @property
        def device_info(self) -> Optional[DeviceInfo]:
            return DeviceInfo(
                identifiers={(DOMAIN, self.entity_id)},
                name=self.name,
                manufacturer=self._device_type,
                model="E-Commerce Integrator Device",
                sw_version=VERSION,
                serial_number=self._device_id,
            )

    @staticmethod
    def device_code() -> str:
        return ""

    @staticmethod
    def device_name() -> str:
        return ""


class CommerceDevice(Entity):
    def __init__(self, entry_id: str):
        self._entry_id: str = entry_id

    @abstractmethod
    def get_orders(self, **kwargs):
        pass
