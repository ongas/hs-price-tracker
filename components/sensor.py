import logging
from datetime import datetime, timedelta

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.price_tracker.components.device import PriceTrackerDevice
from custom_components.price_tracker.components.engine import PriceEngine
from custom_components.price_tracker.components.id import IdGenerator
from custom_components.price_tracker.consts.defaults import DATA_UPDATED
from custom_components.price_tracker.datas.item import ItemData, ItemStatus
from custom_components.price_tracker.datas.price import (
    ItemPriceChangeData,
    create_item_price_change,
)
from custom_components.price_tracker.datas.unit import ItemUnitData, ItemUnitType
from custom_components.price_tracker.utilities.list import Lu

_LOGGER = logging.getLogger(__name__)


class PriceTrackerSensor(RestoreEntity):
    # STATIC
    _attr_icon = "mdi:cart"
    _attr_device_class = "price"
    _attr_should_poll = True

    # Require
    _engine: PriceEngine
    _item_data: ItemData | None = None

    # Custom
    _management_category: str | None = None
    _price_change: ItemPriceChangeData = create_item_price_change(
        updated_at=datetime.now(),
        period_hour=30,
    )
    _refresh_period: int = 30  # minutes
    _unit_type: ItemUnitType = ItemUnitType.PIECE
    _unit_value: int = 1
    _updated_at: datetime | None = None

    def __init__(
        self,
        engine: PriceEngine,
        device: PriceTrackerDevice | None = None,
        unit_type: ItemUnitType = ItemUnitType.PIECE,
        unit_value: int = 1,
        refresh_period: int = 30,
    management_category: str | None = None,
    management_categories: str | None = None,
        debug: bool = False,
    ):
        """Initialize the sensor."""
        self._engine = engine
        self._attr_unique_id = IdGenerator.generate_entity_id(
            self._engine.engine_code(),
            self._engine.entity_id,
            device.device_id if device is not None else None,
        )
        self.entity_id = self._attr_unique_id
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DIAG][PriceTrackerSensor.__init__] entity_id: {self.entity_id}, engine.id_str: {self._engine.id_str()}, engine.entity_id: {self._engine.entity_id}, engine.id: {self._engine.id}")
        self._attr_entity_picture = None
        self._attr_name = self._attr_unique_id
        self._attr_unit_of_measurement = ""
        self._attr_state = STATE_UNKNOWN
        self._attr_available = True
        self._attr_device_info = device.device_info if device is not None else None
        self._attr_extra_state_attributes = {
            "provider": self._engine.engine_code(),
        }

        # Custom
        if management_categories is not None:
            management_categories_list = Lu.map(
                management_categories.split(","), lambda x: str(x).strip()
            )
        else:
            management_categories_list = []

            self._unit_type = unit_type
            self._unit_value = unit_value
            # Defensive: ensure refresh_period is always int
            try:
                self._refresh_period = int(refresh_period) if refresh_period is not None else 30
            except Exception:
                self._refresh_period = 30
            self._updated_at = datetime.now()
            self._management_category = management_category
            self._management_categories = management_categories_list
            self._debug = debug
            self._engine_status = True

    @property
    def engine_id_str(self):
        return self._engine.id_str()

    def _update_engine_status(self, status: bool):
        if self._attr_extra_state_attributes is None:
            self._attr_extra_state_attributes = {}
        self._attr_extra_state_attributes = {
            **self._attr_extra_state_attributes,
            "engine_status": "FETCHED" if status else "ERROR",
        }
        self._engine_status = status

    def _update_updated_at(self):
        self._updated_at = datetime.now()
        self._attr_extra_state_attributes = {
            **self._attr_extra_state_attributes,
            "updated_at": self._updated_at,
        }

    async def async_update(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DIAG][PriceTrackerSensor.async_update] ENTRYPOINT for entity_id={self.entity_id}, unique_id={self._attr_unique_id}, updated_at={self._updated_at}, available={self._attr_available}")
        logger.info(f"[DIAG][PriceTrackerSensor.async_update] _item_data before update: {self._item_data}")
        # Ignore deleted item
        if self._item_data is not None and self._item_data.status == ItemStatus.DELETED:
            self._attr_available = True
            self._update_updated_at()
            return True
        try:
            data = await self._engine.load()
            logger.info(f"[DIAG][PriceTrackerSensor.async_update] Received ItemData: {data}, as_dict: {getattr(data, 'dict', 'no dict') if hasattr(data, 'dict') else str(data)}")

            # Always assign self._item_data after successful engine load
            if data is not None:
                self._item_data = data
                self._item_data = data  # Always assign after successful engine load
                logger.info(f"[DIAG][PriceTrackerSensor.async_update] Assigned self._item_data: {self._item_data}")
                self._price_change = create_item_price_change(
                    updated_at=datetime.now(),
                    period_hour=self._refresh_period,
                    after_price=data.price.price,
                    before_price=self._item_data.price.price if self._item_data is not None else 0.0,
                )
                # Calculate unit
                unit = (
                    ItemUnitData(
                        price=self._item_data.price.price,
                        unit_type=self._unit_type,
                        unit=self._unit_value,
                    )
                    if self._item_data.unit.is_basic
                    else self._item_data.unit
                )
                logger.info(f"[DIAG][PriceTrackerSensor.async_update] Setting state: name={self._item_data.name}, price={self._item_data.price.price}, currency={self._item_data.price.currency}, image={self._item_data.image}")
                logger.info(f"[DIAG][PriceTrackerSensor.async_update] Assigning state: _attr_name={self._item_data.name}, _attr_state={self._item_data.price.price} (type={type(self._item_data.price.price)}), _attr_entity_picture={self._item_data.image}, _attr_unit_of_measurement={self._item_data.price.currency}")
                self._attr_extra_state_attributes = {
                    **self._item_data.dict,
                    **unit.dict,
                    "price_change_status": self._price_change.status.name,
                    "price_change_before_price": self._price_change.before_price,
                    "price_change_after_price": self._price_change.after_price,
                    "management_category": self._management_category,
                    "management_categories": self._management_categories,
                    "updated_at": self._updated_at,
                    "refresh_period": self._refresh_period,
                }
                self._attr_name = self._item_data.name
                price_value = getattr(self._item_data, 'price', None)
                actual_price = getattr(price_value, 'price', None) if price_value is not None else None
                logger.info(f"[DIAG][PriceTrackerSensor.async_update] Extracted price_value: {actual_price} from self._item_data.price: {price_value} (type={type(actual_price)})")
                logger.info(f"[DIAG][PriceTrackerSensor.async_update] Before assignment: self._attr_state={getattr(self, '_attr_state', None)} (type={type(getattr(self, '_attr_state', None))})")
                # Home Assistant expects sensor state as a string or float, but not None or STATE_UNKNOWN
                if actual_price is None or actual_price == STATE_UNKNOWN:
                    logger.warning(f"[DIAG][PriceTrackerSensor.async_update] Invalid price value for state assignment: {actual_price}. Setting state to 0.0 (float).")
                    self._attr_state = 0.0
                else:
                    try:
                        # Try to assign as float if possible
                        self._attr_state = float(actual_price)
                    except Exception as e:
                        logger.warning(f"[DIAG][PriceTrackerSensor.async_update] Failed to convert price to float: {actual_price}, error: {e}. Setting state to 0.0.")
                        self._attr_state = 0.0
                logger.info(f"[DIAG][PriceTrackerSensor.async_update] After assignment: self._attr_state={self._attr_state} (type={type(self._attr_state)})")
                print(f"[DIAG][PriceTrackerSensor.async_update] Final assigned state: {self._attr_state} (type={type(self._attr_state)})", flush=True)
                self._attr_entity_picture = self._item_data.image
                self._attr_available = True
                import pprint
                ui_state_log = f"[DIAG][PriceTrackerSensor.async_update][UI STATE] entity_id={self.entity_id}\nSTATE: {self._attr_state}\nATTRIBUTES:\n{pprint.pformat(self._attr_extra_state_attributes)}"
                logger.info(ui_state_log)
                print(ui_state_log, flush=True)
                try:
                    with open('/tmp/price_tracker_ui_state.log', 'a') as f:
                        f.write(ui_state_log + '\n')
                except Exception as e:
                    logger.warning(f"[DIAG][PriceTrackerSensor.async_update][UI STATE] Failed to write to /tmp/price_tracker_ui_state.log: {e}")
                self._update_engine_status(True)
            else:
                if (
                    self._updated_at is None
                    or self._updated_at + timedelta(hours=6) < datetime.now()
                    or self._debug
                ):
                    self._attr_available = False
                    self._update_engine_status(False)
                else:
                    self._attr_available = True
                    self._update_engine_status(False)
            # ...existing code before except...
        except Exception as e:
            logger.error(f"[DIAG][async_update][BuyWisely] Exception: {e}")
            if (
                self._updated_at is None
                or self._updated_at + timedelta(hours=6) < datetime.now()
                or self._debug
            ):
                self._attr_available = False
                self._update_engine_status(False)
            else:
                self._attr_available = True
                self._update_engine_status(False)
        finally:
            self._update_updated_at()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        _LOGGER.info(f"[DIAG][PriceTrackerSensor.async_added_to_hass] ENTRYPOINT for entity_id={self.entity_id}, unique_id={self._attr_unique_id}")
        # Always force immediate update after entity creation
        await self.async_update()
        async_dispatcher_connect(
            self.hass, DATA_UPDATED, self._schedule_immediate_update
        )
        # If debug mode, schedule repeated updates
        if getattr(self, '_debug', False):
            import asyncio
            async def debug_update_loop():
                while True:
                    await self.async_update()
                    await asyncio.sleep(5)  # Update every 5 seconds in debug mode
            self.hass.async_create_task(debug_update_loop())

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

