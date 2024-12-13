from itertools import product
from math import ceil, floor
from ableton.v3.control_surface.components import ScrollComponent

from ableton.v3.control_surface.component import Component

from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
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
)

from ableton.v3.live.util import find_parent_track, liveobj_valid, clamp

from ableton.v3.control_surface.parameter_mapping_sensitivities import DEFAULT_CONTINUOUS_PARAMETER_SENSITIVITY, DEFAULT_QUANTIZED_PARAMETER_SENSITIVITY

from ableton.v3.control_surface.components.device import get_on_off_parameter

from .Logger import logger

class DeviceSelectControl(ScrollComponent):
    pass

class CustomDeviceNavigationComponent(ScrollComponent):
    bank_size = DEFAULT_BANK_SIZE
    select_buttons = control_list(ButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")
    on_off_buttons = control_list(MappedButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")
    delete_button = ButtonControl()

    _target_track = None
    _devices = []
    _scroll_position = 0
    _selected_index = -1

    @depends(target_track = None)
    def __init__(self, name = "Device_Navigation", target_track = None, *a, **k):
        super().__init__(name = name, *a, **k)

        self._target_track = target_track
        self._on_target_track_changed.subject = self._target_track
        self._on_target_track_changed()

    @property
    def devices(self):
        return self._devices

    @devices.setter
    def devices(self, device_list):
        self._devices = device_list

    @property
    def scroll_position(self):
        return self._scroll_position
    
    @scroll_position.setter
    def scroll_position(self, position):
        self._scroll_position = position
        self._update_on_off_mappings()
        self._update_select_button_state()

    @property
    def selected_index(self):
        return self._selected_index
    
    @selected_index.setter
    def selected_index(self, index):
        self._selected_index = index
        self._update_select_button_state()

    def can_scroll_down(self):
        return self.scroll_position + self.bank_size < ceil(len(self.devices) / float(self.bank_size)) * self.bank_size
    
    def can_scroll_up(self):
        return self.scroll_position - self.bank_size >= 0
    
    def scroll_down(self):
        self.scroll_position += self.bank_size
    
    def scroll_up(self):
        self.scroll_position -= self.bank_size

    def set_prev_group_button(self, control):
        self.set_scroll_up_button(control)

    def set_next_group_button(self, control):
        self.set_scroll_down_button(control)

    @select_buttons.pressed
    def _on_select_buttons_pressed(self, target_button):
        index = target_button.index
        logger.info(f"Select button pressed index = {index}")
        device_index = self.scroll_position + index
        if device_index < len(self.devices):
            if self.delete_button.is_pressed:
                self._target_track.target_track.delete_device(device_index)
            else:
                self.song.view.select_device(self.devices[device_index])

    @listens("target_track")
    def _on_target_track_changed(self):
        logger.info("Target track changed")

        self._on_device_list_changed.subject = self._target_track.target_track
        self._on_selected_device_changed.subject = self._target_track.target_track.view
        self._update_device_list()
        
        if self.selected_index == -1:
            self.scroll_position = 0
        else:
            self.scroll_position = floor(self.selected_index / float(self.bank_size)) * self.bank_size

    @listens("devices")
    def _on_device_list_changed(self):
        logger.info(f"Device list changed length = {len(self._target_track.target_track.devices)}")
        self._update_device_list()

    @listens("selected_device")
    def _on_selected_device_changed(self):
        new_selected_device = self._target_track.target_track.view.selected_device
        prev_selected_device = self.devices[self.selected_index] if self.selected_index != -1 else None

        if new_selected_device != prev_selected_device:
            index = self._find_device_position(self.devices, new_selected_device)
            self.selected_index = index
            logger.info(f"Selected device changed name = {new_selected_device.name}, index = {index}")

    def _update_device_list(self):
        logger.info(f"Devices = {[device.name for device in self._target_track.target_track.devices]}")
        self.devices = self._target_track.target_track.devices
        self.selected_index = self._find_device_position(self.devices, self._target_track.target_track.view.selected_device)
        last_device_index = max(0, len(self.devices) - 1)
        self.scroll_position = clamp(self.scroll_position, 0, floor(last_device_index / float(self.bank_size)) * self.bank_size)
        super().update()

    def _find_device_position(self, devices, target_device):
        for index, device in enumerate(devices):
            if device == target_device:
                return index
        
        return -1
    
    def _update_on_off_mappings(self):
        for button in self.on_off_buttons:
            actual_position = self.scroll_position + button.index
            if actual_position < len(self.devices):
                button.mapped_parameter = get_on_off_parameter(self.devices[actual_position])
            else:
                button.mapped_parameter = None
        
    def _update_select_button_state(self):
        for button in self.select_buttons:
            button.is_on = button.index + self.scroll_position == self.selected_index
