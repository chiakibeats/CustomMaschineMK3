# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================


import json
from pathlib import Path
from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    StepEncoderControl,
    control_matrix
)
from ableton.v3.control_surface.display import Renderable
from ableton.v3.base import (
    clamp,
    depends,
    listenable_property,
    EventObject
)

from ableton.v2.control_surface.internal_parameter import EnumWrappingParameter

from .logger import logger


# Settings schema example
# Bool
# {
#     "key": "bool_option",
#     "description": "Bool Option", # Description should be within 56 characters (MCU display size limit)
#     "type": "bool",
#     "default_value": False,
# },
#
# Integer
# {
#     "key": "integer_option",
#     "description": "Integer Option",
#     "type": "int",
#     "default_value": 2,
#     "min": 0,
#     "max": 100,
# },
#
# Enum (list of strings)
# {
#     "key": "enum_option",
#     "description": "Enum Option",
#     "type": "enum",
#     "default_value": "A",
#     "enum": ["A", "B", "C"],
# },
#
# Special (for display purpose)
# {
#     "key": "__special", # Key name starts with double underscore(__)
#     "description": "I have a message for you",
#     "type": "none",
#     "default_value": "Be creative",
# },
#

class SettingsRepository(EventObject):
    """
    Encapsulation of settings load / store.

    This class uses JSON as serialization format.
    """
    def __init__(self, file_name, schema):
        """
        Args:
            file_name(str): File name of settings JSON file.
            schema(list[dict]): Schema of settings.
        """
        self._file_path = Path(__file__).absolute().parent.joinpath(file_name)
        self._schema = schema
        self._schema_with_key = {}
        for entry in self._schema:
            self._schema_with_key[entry["key"]] = entry
        self._settings = {}
        self.load()

    @property
    def schema(self):
        return self._schema

    @listenable_property
    def value_changed(self):
        """
        Notify setting value changes.

        This property is used for notification only, not for serving actual value.
        Other classes can observe changes of setting option from this property.
        """
        return False

    def load(self):
        if self._file_path.exists():
            try:
                settings = json.loads(self._file_path.read_text())
            except Exception as ex:
                logger.error(f"Error while loading settings: exception = {type(ex).__name__}, args = {ex.args}")
                logger.info(f"Load default settings")
                settings = {}
                
            for key, entry in self._schema_with_key.items():
                if key.startswith("__"):
                    # Ignore special items
                    continue
                elif key in settings:
                    # Sanitize value and load it
                    settings[key] = self.sanitize_value(settings[key], entry)
                else:
                    # Load default value if not exists
                    settings[key] = entry["default_value"]
            
            self._settings = settings
        else:
            self.clear_settings()
            self.save()

    def save(self):
        with self._file_path.open("w") as settings_file:
            settings_file.write(json.dumps(self._settings, indent = 4))

    def clear_settings(self):
        for key, entry in self._schema_with_key.items():
            if entry["key"].startswith("__"):
                # Skip options which start with double underscore(__)
                pass
            else:
                self._settings[entry["key"]] = entry["default_value"]

    def sanitize_value(self, value, entry):
        """
        Convert raw string value to actual type value with sanitization.

        Args:
            value(any): Value to sanitize.
            entry(dict): Setting schema entry corresponding to `value`.

        Returns:
            value:
                If the raw value follows schema, this function just converts value type.
                Otherwise returns the default value defined in schema.
        """
        value_type = entry["type"]
        if value_type == "bool":
            if isinstance(value, bool):
                return value
        elif value_type == "int":
            try:
                value = int(value)
                if value >= entry["min"] and value <= entry["max"]:
                    return value
            except:
                pass
        elif value_type == "enum":
            try:
                value = str(value)
                if value in entry["enum"]:
                    return value
            except:
                pass

        return entry["default_value"]
        
    def set_value(self, key, value):
        if key in self._schema_with_key:
            self._settings[key] = self.sanitize_value(value, self._schema_with_key[key])
        
        self.notify_value_changed()

    def get_value(self, key):
        if key.startswith("__"):
            return self._schema_with_key[key]["default_value"]
        else:
            return self._settings[key]

class SettingsComponent(Component, Renderable):
    """
    User interface for viewing / modifying settings.
    """
    select_encoder = StepEncoderControl(num_steps = 64)
    """Setting option scroll encoder."""
    value_encoder = StepEncoderControl(num_steps = 8)
    """Option value scroll encoder."""

    @depends(settings = None)
    def __init__(self, name = "Settings", settings = None, *a, **k):
        """
        Args:
            name(str):
                Component name. This should keep default.
            settings(SettingsRepository):
                Repository of settings. DI container will supply actual value.
        """
        super().__init__(name, *a, **k)

        self._current_index = 0
        self._settings = settings
        self._schema = self._settings.schema

    @listenable_property
    def current_description(self):
        return self._schema[self._current_index]["description"]
    
    @listenable_property
    def current_value(self):
        key = self._schema[self._current_index]["key"]
        if key.startswith("__"):
            return self._schema[self._current_index]["default_value"]
        else:
            return self._settings.get_value(key)

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        """
        Change the selection of the setting item to be displayed.

        Args:
            value(int): Offset to move the selection.
            encoder(StepEncoderControl): Control object that triggered this event.
        """
        self._current_index = clamp(self._current_index + value, 0, len(self._schema) - 1)
        logger.info(f"Select setting {self.current_description}")
        self.notify_current_description()
        self.notify_current_value()

    @value_encoder.value
    def _on_value_encoder_value(self, value, encoder):
        """
        Change the option value of the selected setting item.

        Any changes will send notification instantly.
        But the contents of settings file doesn't change until calling `save()` method.

        Args:
            value(int): Offset to move the selection.
            encoder(StepEncoderControl): Encoder control that triggered this event.
        """
        schema = self._schema[self._current_index]
        current_value = self._settings.get_value(schema["key"])
        type = schema["type"]

        # Move forward or backward the option value by following the schema.
        if type == "bool":
            new_value = bool(clamp(int(current_value) + value, 0, 1))
            self._settings.set_value(schema["key"], new_value)
        elif type == "int":
            new_value = clamp(int(current_value + value), schema["min"], schema["max"])
            self._settings.set_value(schema["key"], new_value)
        elif type == "enum":
            index = -1
            options = schema["enum"]
            for i in range(len(options)):
                if options[i] == current_value:
                    index = i
                    break

            new_value = clamp(int(index + value), 0, len(options) - 1)
            self._settings.set_value(schema["key"], schema["enum"][new_value])
        elif type == "none":
            # ignore
            pass

        self.notify_current_value()
