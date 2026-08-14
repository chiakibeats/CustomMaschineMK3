# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2026 chiaki
#
# ==================================================

from ableton.v3.base import (
    listens,
    sign,
    listenable_property,
    EventObject
)
from ableton.v2.base import EventError
from ableton.v2.control_surface import WrappingParameter, EnumWrappingParameter
from ableton.v3.live.util import liveobj_valid

from Live.Base import Timer # type: ignore

from .logger import logger

# Max clip length (from Push 2)
MAX_CLIP_LENGTH = 365 * 24 * 3600 * 2.0

def bool_to_display_value(value, off_value, on_value):
    return on_value if value else off_value

class BoolWrappingParameter(WrappingParameter):
    """
    Python property wrapper especially for `bool`.

    This class is used for modifying property from `MappedSensitivitySettingControl` and `MappedButtonControl`.
    """
    is_enaled = True
    is_quantized = True

    def __init__(self,
        property_host,
        source_property,
        display_value_conversion,
        invert = False, *a, **k):
        super().__init__(
            property_host,
            source_property,
            self._from_bool_invert if invert else self._from_bool,
            self._to_bool_invert if invert else self._to_bool,
            display_value_conversion,
            [], *a, **k)
        self._parent = property_host

    def set_property_host(self, new_host):
        super().set_property_host(new_host)
        self._parent = new_host
        self.notify_value()

    def _to_bool(self, value, parent):
        return bool(value)
    
    def _from_bool(self, value, parent):
        return int(value)
    
    def _to_bool_invert(self, value, parent):
        return not bool(value)
    
    def _from_bool_invert(self, value, parent):
        return int(not value)

    @property
    def min(self):
        return 0

    @property
    def max(self):
        return 1
    
class CustomEnumWrappingParameter(EnumWrappingParameter):
    """
    Extended Python property wrapper especially for enum.

    This version has:
        - Replace property host method
        - Replace value host (data source of available choices) method
    """
    def __init__(self,
        index_property_host = None,
        values_host = None,
        values_property = None,
        index_property = None,
        value_type = int,
        to_index_conversion = None,
        from_index_conversion = None, *a, **k):
        super().__init__(
            index_property_host,
            index_property_host,
            values_host,
            values_property,
            index_property,
            value_type,
            to_index_conversion,
            from_index_conversion, *a, **k)

    def set_property_host(self, new_host):
        super().set_property_host(new_host)
        self._parent = new_host
        self.notify_value()

    def set_values_host(self, new_host):
        self._values_host = new_host
        try:
            self.register_slot(self._values_host, self.notify_value_items, self._values_property)
        except EventError:
            pass
    
class BeatOrTimeWrappingParameter(WrappingParameter):
    """
    Python property wrapper especially for clip time / length parameters.

    This was abandoned, maybe delete it later.
    """
    min = -MAX_CLIP_LENGTH
    max = MAX_CLIP_LENGTH

    def __init__(self, property_host, source_property, display_value_conversion, *a, **k):
        super().__init__(
            property_host = property_host,
            source_property = source_property,
            display_value_conversion = display_value_conversion, *a, **k)
        self._parent = property_host

    @listens("signature_denominator")
    def _on_denominator_changed(self):
        pass

    @listens("signature_numerator")
    def _on_numerator_changed(self):
        pass

    @listens("warping")
    def _on_warping_changed(self):
        pass

class CustomValueStepper():
    """
    Convert continous value movement to stepped movement.

    Also, this can change step count dynamically.
    """
    _step_count = 0
    _step_value = 0.0

    def __init__(self, step_count = 64):
        self._step_count = step_count

    @property
    def step_count(self):
        return self._step_count
    
    @step_count.setter
    def step_count(self, value):
        self._step_count = value
        self.reset()

    def update(self, value):
        if sign(value) != sign(self._step_value):
            self.reset()

        new_step_value = self._step_value + value * self._step_count
        if int(new_step_value) != int(self._step_value):
            self.reset()
            return int(new_step_value)
        else:
            self._step_value = new_step_value

        return 0
    
    def reset(self):
        self._step_value = 0.0

class LEDBlinker(EventObject):
    """
    Timer and flag management for LED blinking.
    """
    def __init__(self, blink_time = 0.5):
        self._blink_time = blink_time * 1000
        self._blink_state = True
        self._timer = Timer(callback = self.timer_callback, interval = int(self._blink_time), start = True)

    @listenable_property
    def blink_state(self):
        return self._blink_state

    def timer_callback(self):
        self._blink_state = not self._blink_state
        #logger.info(f"Blink state = {self._blink_state}")
        self._timer.restart()
        self.notify_blink_state()

