# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.control_surface.elements import SysexElement
from .logger import logger

class SysexShiftButton(SysexElement):
    """
    Sysex button with message forwarding to normal `ButtonElement`.
    """
    def __init__(self, target_button, *a, **k):
        """
        Args:
            target_button(ButtonElement): Target of MIDI message forwarding.
        """
        super().__init__(*a, **k)
        self._target_button = target_button
        # TODO: Delete this variable because of not used.
        self._last_receive_value = None

    @property
    def target_button(self):
        """Get or set target of message forwarding."""
        return self._target_button
    
    @target_button.setter
    def target_button(self, value):
        self._target_button = value
        self._last_receive_value = None

    def receive_value(self, value):
        super().receive_value(value)
        value = value[0]
        logger.info(f"Shift = {value}")
        self._last_receive_value = value

        if self.target_button:
            self.target_button.receive_value(value)
