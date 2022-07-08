"""Support to manage a Dictionary helper."""
from __future__ import annotations

import ast
import logging

import voluptuous as vol

from homeassistant.const import (
    ATTR_EDITABLE,
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    SERVICE_RELOAD,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import collection
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.integration_platform import (
    async_process_integration_platform_for_component,
)
from homeassistant.helpers.restore_state import RestoreEntity
import homeassistant.helpers.service
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "input_dictionary"

CONF_DICTIONARY_STR = "keyvalues"

ATTR_DICTIONARY = "dictionary"
ATTR_KEYVALUES = CONF_DICTIONARY_STR
ATTR_KEY = "key"

SERVICE_APPEND_DICTIONARY = "append_dictionary"
SERVICE_REMOVE_KEYVALUE = "remove_key"
SERVICE_RESET_DICTIONARY = "reset_dictionary"

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1


def _cv_input_text(cfg: ConfigType) -> ConfigType:
    """Configure validation helper for input number (voluptuous)."""
    # if not isinstance(ast.literal_eval(cfg.get(CONF_DICTIONARY_STR)), dict):
    #     raise vol.Invalid(
    #         "Configuration does not contain a valid dictionary string input."
    #     )
    return cfg


CREATE_FIELDS = {
    vol.Required(CONF_NAME): vol.All(str, vol.Length(min=1)),
    vol.Optional(CONF_DICTIONARY_STR): cv.string,
    vol.Optional(CONF_ICON): cv.icon,
}
UPDATE_FIELDS = {
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_DICTIONARY_STR): cv.string,
    vol.Optional(CONF_ICON): cv.icon,
}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: cv.schema_with_slug_keys(
            vol.All(
                {
                    vol.Optional(CONF_NAME): cv.string,
                    vol.Optional(CONF_DICTIONARY_STR): cv.string,
                    vol.Optional(CONF_ICON): cv.icon,
                },
                _cv_input_text,
            ),
        )
    },
    extra=vol.ALLOW_EXTRA,
)
RELOAD_SERVICE_SCHEMA = vol.Schema({})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up an input dictionary."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    # Process integration platforms right away since
    # we will create entities before firing EVENT_COMPONENT_LOADED
    await async_process_integration_platform_for_component(hass, DOMAIN)

    id_manager = collection.IDManager()

    yaml_collection = collection.YamlCollection(
        logging.getLogger(f"{__name__}.yaml_collection"), id_manager
    )
    collection.sync_entity_lifecycle(
        hass, DOMAIN, DOMAIN, component, yaml_collection, InputDictionary.from_yaml
    )

    storage_collection = InputDictionaryStorageCollection(
        Store(hass, STORAGE_VERSION, STORAGE_KEY),
        logging.getLogger(f"{__name__}.storage_collection"),
        id_manager,
    )
    collection.sync_entity_lifecycle(
        hass, DOMAIN, DOMAIN, component, storage_collection, InputDictionary
    )

    await yaml_collection.async_load(
        [{CONF_ID: id_, **(conf or {})} for id_, conf in config.get(DOMAIN, {}).items()]
    )
    await storage_collection.async_load()

    collection.StorageCollectionWebsocket(
        storage_collection, DOMAIN, DOMAIN, CREATE_FIELDS, UPDATE_FIELDS
    ).async_setup(hass)

    async def reload_service_handler(service_call: ServiceCall) -> None:
        """Reload yaml entities."""
        conf = await component.async_prepare_reload(skip_reset=True)
        if conf is None:
            conf = {DOMAIN: {}}
        await yaml_collection.async_load(
            [{CONF_ID: id_, **(cfg or {})} for id_, cfg in conf.get(DOMAIN, {}).items()]
        )

    homeassistant.helpers.service.async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_RELOAD,
        reload_service_handler,
        schema=RELOAD_SERVICE_SCHEMA,
    )

    component.async_register_entity_service(
        SERVICE_APPEND_DICTIONARY,
        {vol.Required(ATTR_KEYVALUES): cv.string},
        "async_append_dictionary",
    )
    component.async_register_entity_service(
        SERVICE_REMOVE_KEYVALUE,
        {vol.Required(ATTR_KEY): cv.string},
        "async_remove_key",
    )
    component.async_register_entity_service(
        SERVICE_RESET_DICTIONARY, {}, "async_reset_dictionary"
    )

    return True


class InputDictionaryStorageCollection(collection.StorageCollection):
    """Input storage based collection."""

    CREATE_SCHEMA = vol.Schema(vol.All(CREATE_FIELDS, _cv_input_text))
    UPDATE_SCHEMA = vol.Schema(UPDATE_FIELDS)

    async def _process_create_data(self, data: dict) -> dict:
        """Validate the config is valid."""
        return self.CREATE_SCHEMA(data)

    @callback
    def _get_suggested_id(self, info: dict) -> str:
        """Suggest an ID based on the config."""
        return str(info[CONF_NAME])

    async def _update_data(self, data: dict, update_data: dict) -> dict:
        """Return a new updated data object."""
        update_data = self.UPDATE_SCHEMA(update_data)
        return _cv_input_text({**data, **update_data})


class InputDictionary(RestoreEntity):
    """Represent a Dictionary."""

    def __init__(self, config: dict) -> None:
        """Initialize Dictionary obj."""
        self._config = config
        self.editable = True
        self.dictionary: dict = {}
        self.keyvalues: str = ""

    @classmethod
    def from_yaml(cls, config: dict) -> InputDictionary:
        """Return entity instance initialized from yaml storage."""
        input_dictionary = cls(config)
        input_dictionary.entity_id = f"{DOMAIN}.{config[CONF_ID]}"
        input_dictionary.editable = False
        input_dictionary.keyvalues = str(config.get(CONF_DICTIONARY_STR))
        if len(input_dictionary.keyvalues) > 0:
            input_dictionary.dictionary = ast.literal_eval(input_dictionary.keyvalues)
        else:
            input_dictionary.dictionary = {}
        return input_dictionary

    @property
    def should_poll(self):
        """If entity should be polled."""
        return False

    @property
    def name(self):
        """Return the name of the text input entity."""
        return self._config.get(CONF_NAME)

    @property
    def icon(self):
        """Return the icon to be used for this entity."""
        return self._config.get(CONF_ICON)

    @property
    def dictionarystr(self) -> str:
        """Return min len of the text."""
        return self.keyvalues

    @property
    def state(self):
        """Return the state of the component."""
        return self.dictionary

    @property
    def unique_id(self) -> str | None:
        """Return unique id for the entity."""
        return str(self._config[CONF_ID])

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_EDITABLE: self.editable,
            ATTR_DICTIONARY: self.dictionary,
            ATTR_KEYVALUES: self.keyvalues,
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if state := await self.async_get_last_state():
            self._parse_restored_state(state)

        if self.dictionary is not None:
            return

    async def async_append_dictionary(self, keyvalues: str):
        """Provide a string to update the dictionary."""
        self.keyvalues = keyvalues
        if self.dictionary is None:
            self.dictionary = {}
        self.dictionary.update(ast.literal_eval(keyvalues))
        self.async_write_ha_state()

    async def async_remove_key(self, key):
        """Remove provided keys from the dictionary."""
        if self.dictionary is None:
            _LOGGER.error("Dictionary object is null. Service remove_key has failed")
            return

        self.dictionary.pop(key)
        self.async_write_ha_state()

    async def async_reset_dictionary(self) -> None:
        """Reset the dictionary."""
        self.dictionary.clear()
        self.async_write_ha_state()

    async def async_update_config(self, config: dict) -> None:
        """Handle when the config is updated."""
        self._config = config
        self.async_write_ha_state()

    @callback
    def _parse_restored_state(self, state):
        self.editable = state.attributes.get(ATTR_EDITABLE)
        self.dictionary = state.attributes.get(ATTR_DICTIONARY)
        self.keyvalues = state.attributes.get(ATTR_KEYVALUES)
