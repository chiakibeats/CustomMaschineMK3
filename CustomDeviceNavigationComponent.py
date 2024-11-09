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
    device_select_buttons = control_list(ButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")
    device_on_off_buttons = control_list(MappedButtonControl, control_count = bank_size, color = "DefaultButton.Off", on_color = "DefaultButton.On")

    _selected_track = None
    _devices = []
    _scroll_position = 0
    _selected_index = -1

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.register_slot(self.song.view, self._on_selected_track_changed, "selected_track")
        self._on_selected_track_changed()

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
        self._update_radio_button_state()

    @property
    def selected_index(self):
        return self._selected_index
    
    @selected_index.setter
    def selected_index(self, index):
        self._selected_index = index
        self._update_radio_button_state()

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

    @device_select_buttons.pressed
    def _on_device_select_buttons_pressed(self, target_button):
        for index in range(self.bank_size):
            if self.device_select_buttons[index] == target_button:
                logger.info(f"Select button pressed index = {index}")
                new_selected_index = self.scroll_position + index
                if new_selected_index < len(self.devices):
                    self.song.view.select_device(self.devices[new_selected_index])

    def _on_selected_track_changed(self):
        logger.info("Selected track changed")

        self._selected_track = self.song.view.selected_track
        self._on_device_list_changed.subject = self._selected_track
        self._on_selected_device_changed.subject = self._selected_track.view
        self._update_device_list()
        
        if self.selected_index == -1:
            self.scroll_position = 0
        else:
            self.scroll_position = floor(self.selected_index / float(self.bank_size)) * self.bank_size

    @listens("devices")
    def _on_device_list_changed(self):
        logger.info(f"Device list changed length = {len(self.song.view.selected_track.devices)}")
        self._update_device_list()

    @listens("selected_device")
    def _on_selected_device_changed(self):
        new_selected_device = self._selected_track.view.selected_device
        prev_selected_device = self.devices[self.selected_index] if self.selected_index != -1 else None

        if new_selected_device != prev_selected_device:
            index = self._find_device_position(self.devices, new_selected_device)
            self.selected_index = index
            logger.info(f"Selected device changed name = {self.song.view.selected_track.view.selected_device.name}, index = {index}")

    def _update_device_list(self):
        logger.info(f"Devices = {[device.name for device in self._selected_track.devices]}")
        self.devices = self._selected_track.devices
        self.selected_index = self._find_device_position(self.devices, self._selected_track.view.selected_device)
        last_device_index = max(0, len(self.devices) - 1)
        self.scroll_position = clamp(self.scroll_position, 0, floor(last_device_index / float(self.bank_size)) * self.bank_size)
        super().update()

    def _find_device_position(self, devices, target_device):
        for index, device in enumerate(devices):
            if device == target_device:
                return index
        
        return -1
    
    def _update_on_off_mappings(self):
        for index in range(self.bank_size):
            actual_position = self.scroll_position + index
            if actual_position < len(self.devices):
                self.device_on_off_buttons[index].mapped_parameter = get_on_off_parameter(self.devices[actual_position])
            else:
                self.device_on_off_buttons[index].mapped_parameter = None
        
    def _update_radio_button_state(self):
        for index in range(self.bank_size):
            new_state = index + self.scroll_position == self.selected_index
            button = self.device_select_buttons[index]
            if button.is_on != new_state:
                button.is_on = new_state


