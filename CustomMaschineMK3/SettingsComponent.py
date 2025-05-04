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
)

from .Logger import logger

def beat_ratio(denominator):
    return 4.0 / denominator

SETTING_FILE_NAME = "preferences.json"
BASE_LENGTH_LIST = [1, 2, 4, 8, 16, 32, 64, 128]

NOTE_REPEAT_RATES = []
NOTE_REPEAT_RATES += [(beat_ratio(l), f"1/{l}") for l in BASE_LENGTH_LIST]
NOTE_REPEAT_RATES += [(beat_ratio(l * 1.5), f"1/{l}T") for l in BASE_LENGTH_LIST]
NOTE_REPEAT_RATES += [(beat_ratio(l) * 1.5, f"1/{l}D") for l in BASE_LENGTH_LIST]

REPEAT_RATE_KEYS = [x[1] for x in NOTE_REPEAT_RATES]

# Settings scheme example
# Bool ()
# {
#     "key": "bool_option",
#     "description": "Bool Option",
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
# Special (display only)
# {
#     "key": "__special", # must starts with double underscore(__)
#     "description": "I have a message for you",
#     "type": "none",
#     "default_value": "Be creative",
# },
#

SETTINGS = [
    {
        "key": "auto_switch_selector",
        "description": "Auto Switch Repeat Rate Selector",
        "type": "bool",
        "default_value": False,
    },
    {
        "key": "repeat_rate_a",
        "description": "Note Repeat Rate A",
        "type": "enum",
        "default_value": "1/4",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_b",
        "description": "Note Repeat Rate B",
        "type": "enum",
        "default_value": "1/8",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_c",
        "description": "Note Repeat Rate C",
        "type": "enum",
        "default_value": "1/16",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_d",
        "description": "Note Repeat Rate D",
        "type": "enum",
        "default_value": "1/32",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_e",
        "description": "Note Repeat Rate E",
        "type": "enum",
        "default_value": "1/4T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_f",
        "description": "Note Repeat Rate F",
        "type": "enum",
        "default_value": "1/8T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_g",
        "description": "Note Repeat Rate G",
        "type": "enum",
        "default_value": "1/16T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "repeat_rate_h",
        "description": "Note Repeat Rate H",
        "type": "enum",
        "default_value": "1/32T",
        "enum": REPEAT_RATE_KEYS,
    },
    {
        "key": "sequencer_style",
        "description": "Sequencer Pad Style",
        "type": "enum",
        "default_value": "Maschine",
        "enum": ["Maschine", "Push"]
    },
    {
        "key": "__version",
        "description": "CustomMaschineMK3 by chiaki",
        "type": "none",
        "default_value": "Version 1.1",
    },    
]

class SettingsRepository:
    def __init__(self, file_name = SETTING_FILE_NAME, scheme = SETTINGS):
        self._file_path = Path(__file__).absolute().parent.joinpath(file_name)
        self._scheme = scheme
        self._settings = {}
        self.load()

    def load(self):
        if self._file_path.exists():
            self._settings = json.loads(self._file_path.read_text())
        else:
            self.clear_settings()
            self.save()

    def save(self):
        with self._file_path.open("w") as settings_file:
            settings_file.write(json.dumps(self._settings, indent = 4))

    def clear_settings(self):
        for entry in self._scheme:
            if not entry["key"].startswith("__"):
                self._settings[entry["key"]] = entry["default_value"]

    def set_value(self, key, value):
        # must be sanitized
        self._settings[key] = value

    def get_value(self, key):
        if key.startswith("__"):
            for entry in self._scheme:
                if entry["key"] == key:
                    return entry["default_value"]
        else:
            # must be sanitized
            return self._settings[key]

class SettingsComponent(Component, Renderable):
    select_encoder = StepEncoderControl(num_steps = 64)
    value_encoder = StepEncoderControl(num_steps = 8)

    @depends(settings = None)
    def __init__(self, name = "Settings", settings = None, scheme = SETTINGS, *a, **k):
        super().__init__(name, *a, **k)

        self._current_index = 0
        self._scheme = scheme
        self._settings = settings

    @listenable_property
    def current_description(self):
        return self._scheme[self._current_index]["description"]
    
    @listenable_property
    def current_value(self):
        key = self._scheme[self._current_index]["key"]
        if key.startswith("__"):
            return self._scheme[self._current_index]["default_value"]
        else:
            return self._settings.get_value(key)

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        self._current_index = clamp(self._current_index + value, 0, len(self._scheme) - 1)
        logger.info(f"Select setting {self.current_description}")
        self.notify_current_description()
        self.notify_current_value()

    @value_encoder.value
    def _on_value_encoder_value(self, value, encoder):
        scheme = self._scheme[self._current_index]
        current_value = self._settings.get_value(scheme["key"])
        type = scheme["type"]

        if type == "bool":
            new_value = bool(clamp(int(current_value) + value, 0, 1))
            self._settings.set_value(scheme["key"], new_value)
        elif type == "int":
            new_value = clamp(int(current_value + value), scheme["min"], scheme["max"])
            self._settings.set_value(scheme["key"], new_value)
        elif type == "enum":
            index = -1
            options = scheme["enum"]
            for i in range(len(options)):
                if options[i] == current_value:
                    index = i
                    break

            new_value = clamp(int(index + value), 0, len(options) - 1)
            self._settings.set_value(scheme["key"], scheme["enum"][new_value])
        elif type == "none":
            # ignore
            pass


        self.notify_current_value()
