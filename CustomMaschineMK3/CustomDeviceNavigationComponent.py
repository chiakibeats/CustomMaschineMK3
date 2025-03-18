# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from itertools import product
from math import ceil, floor
from ableton.v3.control_surface.components import ScrollComponent

from ableton.v3.control_surface.component import Component

from ableton.v3.control_surface.controls import (
    ButtonControl,
    StepEncoderControl,
    TouchControl,
    MappedButtonControl,
    SendValueInputControl,
    SendValueEncoderControl,
    FixedRadioButtonGroup,
    control_matrix,
    control_list
)

from ableton.v2.control_surface.control import (
    MatrixControl
)

from ableton.v2.control_surface import (
    WrappingParameter
)

from ableton.v3.control_surface import (
    DEFAULT_BANK_SIZE,
    ScriptForwarding,
)

from ableton.v3.base import (
    depends,
    listens,
    listenable_property,
    index_if,
)

from ableton.v3.live.util import find_parent_track, liveobj_valid, clamp
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.parameter_mapping_sensitivities import DEFAULT_CONTINUOUS_PARAMETER_SENSITIVITY, DEFAULT_QUANTIZED_PARAMETER_SENSITIVITY
from ableton.v3.control_surface.components.device import get_on_off_parameter
from ableton.v3.control_surface.components.device_navigation import DeviceNavigationComponent

from .Logger import logger

class CustomDeviceNavigationComponent(DeviceNavigationComponent):
    bank_size = DEFAULT_BANK_SIZE
    select_buttons = control_list(ButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")
    on_off_buttons = control_list(MappedButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")
    delete_button = ButtonControl(color = None)
    view_button = ButtonControl(color = None)
    select_encoder = StepEncoderControl(num_steps = 64)

    _scroll_position = 0

    def __init__(self, name = "Device_Navigation", item_provider = None, *a, **k):
        super().__init__(name = name, item_provider = item_provider, *a, **k)
        self.register_slot(self._item_provider, self._on_device_chain_changed, "items")
        self.register_slot(self._item_provider, self._on_selected_item_changed, "selected_item")
        self.register_slot(self.song, self._on_selected_item_changed, "appointed_device")

    @property
    def devices(self):
        return self._item_provider.items

    @property
    def scroll_position(self):
        return self._scroll_position
    
    @scroll_position.setter
    def scroll_position(self, position):
        self._scroll_position = position
        self._update_on_off_mappings()
        self._update_select_button_state()

    def can_scroll_down(self):
        return self.scroll_position + self.bank_size < ceil(len(self._item_provider.items) / float(self.bank_size)) * self.bank_size
    
    def can_scroll_up(self):
        return self.scroll_position - self.bank_size >= 0
    
    def scroll_down(self):
        self.scroll_position += self.bank_size
    
    def scroll_up(self):
        self.scroll_position -= self.bank_size

    def set_prev_page_button(self, control):
        self.set_scroll_up_button(control)

    def set_next_page_button(self, control):
        self.set_scroll_down_button(control)

    @select_buttons.pressed
    def _on_select_buttons_pressed(self, target_button):
        index = target_button.index
        logger.info(f"Select button pressed index = {index}")
        device_index = self.scroll_position + index
        if device_index < len(self._item_provider.items):
            target_device = self._item_provider.items[device_index]
            if self.delete_button.is_pressed:
                # Find target device from parent chain to get index
                device_parent = target_device.canonical_parent
                logger.info(f"Device parent = {device_parent}")
                index_in_chain = -1
                for index, device in enumerate(device_parent.devices):
                    if device == target_device:
                        index_in_chain = index
                        break
                
                if index_in_chain != -1:
                    device_parent.delete_device(index_in_chain)
                
            elif self.view_button.is_pressed:
                target_device.view.is_collapsed = not target_device.view.is_collapsed
            else:
                self.song.view.select_device(target_device)
                self.notify(self.notifications.Device.select, target_device.name)

    @select_encoder.value
    def _on_select_encoder_value_changed(self, value, encoder):
        selected_device = self.song.view.selected_track.view.selected_device
        current_index = self._item_provider.items.index(selected_device)
        new_index = clamp(current_index + value, 0, len(self._item_provider.items) - 1)
        target_device = self._item_provider.items[new_index]
        self.song.view.select_device(target_device)
        self.notify(self.notifications.Device.select, target_device.name)

    def _on_device_chain_changed(self):
        logger.info("Device chain changed")
        logger.info(f"Devices = {[device.name for device in self._item_provider.items]}")
        
        if self._item_provider.selected_index == -1:
            self.scroll_position = 0
        else:
            self.scroll_position = floor(self._item_provider.selected_index / float(self.bank_size)) * self.bank_size

        self._update_on_off_mappings()
        self._update_select_button_state()

    def _on_selected_item_changed(self):
        logger.info(f"Selected device changed index = {self._item_provider.selected_index}")
        self._update_select_button_state()
    
    def _update_on_off_mappings(self):
        for button in self.on_off_buttons:
            actual_position = self.scroll_position + button.index
            if actual_position < len(self._item_provider.items):
                button.mapped_parameter = get_on_off_parameter(self._item_provider.items[actual_position])
            else:
                button.mapped_parameter = None
        
    def _update_select_button_state(self):
        selected_device = self.song.appointed_device
        selected_index = index_if(lambda d: d == selected_device, self._item_provider.items)
        if selected_index == len(self._item_provider.items):
            selected_index = -1
        
        for button in self.select_buttons:
            button.is_on = button.index + self.scroll_position == selected_index
