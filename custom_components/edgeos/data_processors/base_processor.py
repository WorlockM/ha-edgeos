import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify

from ..common.consts import (
    API_DATA_SYSTEM,
    DATA_SYSTEM_SYSTEM,
    DEFAULT_NAME,
    SYSTEM_DATA_HOSTNAME,
)
from ..common.enums import DeviceTypes
from ..models.config_data import ConfigData

_LOGGER = logging.getLogger(__name__)


class BaseProcessor:
    _api_data: dict | None = None
    _ws_data: dict | None = None
    _config_data: ConfigData | None = None
    _unique_messages: list[str] | None = None
    processor_type: DeviceTypes | None = None
    _hostname: str | None = None

    def __init__(self, config_data: ConfigData):
        self._config_data = config_data

        self._api_data = None
        self._ws_data = None
        self.processor_type = None
        self._hostname = None

        self._unique_messages = []

    def update(self, api_data: dict, ws_data: dict):
        self._api_data = api_data
        self._ws_data = ws_data

        self._process_api_data()
        self._process_ws_data()

    def _process_api_data(self):
        system_section = self._api_data.get(API_DATA_SYSTEM, {})
        system_details = system_section.get(DATA_SYSTEM_SYSTEM, {})

        self._hostname = system_details.get(SYSTEM_DATA_HOSTNAME).upper()

    def _process_ws_data(self):
        pass

    def _unique_log(self, log_level: int, message: str):
        if message not in self._unique_messages:
            self._unique_messages.append(message)

            _LOGGER.log(log_level, message)

    @property
    def via_identifier(self) -> tuple[str, str] | None:
        """Identifier of the parent (system) device, None if there is none."""
        if self._hostname is None:
            return None

        return DEFAULT_NAME, self._hostname

    def get_device_name(self, item_id: str | None = None) -> str:
        """Name of the device, as used in its device info."""
        return self._get_device_info_name(self._get_device_key(item_id))

    def get_device_identifier(self, item_id: str | None = None) -> tuple[str, str]:
        """Identifier of the device, as used in its device info."""
        unique_id = self._get_device_info_unique_id(self._get_device_key(item_id))

        return DEFAULT_NAME, unique_id

    def get_device_info(
        self, item_id: str | None = None, via_device_id: str | None = None
    ) -> DeviceInfo:
        # Only pass via_device_id when the parent is known: an explicit None
        # would remove an existing link in the device registry.
        via_link = {} if via_device_id is None else {"via_device_id": via_device_id}

        device_info = DeviceInfo(
            identifiers={self.get_device_identifier(item_id)},
            name=self.get_device_name(item_id),
            model=self.processor_type,
            manufacturer=DEFAULT_NAME,
            **via_link,
        )

        return device_info

    def _get_device_key(self, item_id: str | None = None) -> str | None:
        """The part of the device name and identifier that identifies the item."""
        return item_id

    def _get_device_info_name(self, item_id: str | None = None):
        parts = [self._hostname, self.processor_type, item_id]

        relevant_parts = [part for part in parts if part is not None]

        name = " ".join(relevant_parts)

        return name

    def _get_device_info_unique_id(self, item_id: str | None = None):
        identifier = self._get_device_info_name(item_id)

        unique_id = slugify(identifier)

        return unique_id
