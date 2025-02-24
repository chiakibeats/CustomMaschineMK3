# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.base import listens, listenable_property, task, EventObject
from ableton.v3.control_surface.controls import ButtonControl, control_list
from ableton.v3.control_surface.display import Renderable

class KnobTouchStateMixin(EventObject, Renderable):
    knob_touch_buttons = control_list(ButtonControl, color = None)

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._active_index = -1
        self._inactive_task = self._tasks.add(task.sequence(task.wait(0.3), task.run(self._inactive_parameter_index)))
        self._inactive_task.kill()

    @listenable_property
    def active_index(self):
        return self._active_index
    
    @active_index.setter
    def active_index(self, index):
        self._active_index = index
        self.notify_active_index()

    def _inactive_parameter_index(self):
        self.active_index = -1

    @knob_touch_buttons.pressed
    def __on_knob_touch_pressed(self, button):
        if self.active_index == -1 or self._inactive_task.is_running:
            self._inactive_task.kill()
            self.active_index = button.index
        self.on_knob_touch_pressed(button)

    def on_knob_touch_pressed(self, button):
        pass
    
    @knob_touch_buttons.pressed_delayed
    def __on_knob_touch_pressed_delayed(self, button):
        self.on_knob_touch_pressed_delayed(button)

    def on_knob_touch_pressed_delayed(self, button):
        pass
    
    @knob_touch_buttons.released
    def __on_knob_touch_released(self, target_button):
        touched_index = -1
        for button in self.knob_touch_buttons:
            if button.is_pressed:
                touched_index = button.index
        
        if touched_index != -1:
            self.active_index = touched_index
        else:
            self._inactive_task.restart()
        self.on_knob_touch_released(button)
    
    def on_knob_touch_released(self, button):
        pass

    @knob_touch_buttons.released_immediately
    def __on_knob_touch_released_immediately(self, button):
        self.on_knob_touch_released_immediately(button)

    def on_knob_touch_released_immediately(self, button):
        pass

    @knob_touch_buttons.released_delayed
    def __on_knob_touch_released_delayed(self, button):
        self.on_knob_touch_released_delayed(button)

    def on_knob_touch_released_delayed(self, button):
        pass

    @knob_touch_buttons.double_clicked
    def __on_knob_touch_double_clicked(self, button):
        self.on_knob_touch_double_clicked(button)

    def on_knob_touch_double_clicked(self, button):
        pass
