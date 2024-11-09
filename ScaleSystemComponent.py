from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import (
    EncoderControl,
    ButtonControl,
    control_list
)
from ableton.v3.live.util import liveobj_valid
from ableton.v3.base import listens

class ScaleSystemComponent(Component):
    select_encoder = EncoderControl()
    scale_toggle_button = ButtonControl()

    # Just for LED feedback
    scale_indicator_buttons = control_list(ButtonControl, color = None)

    def __init__(self, name='ScaleSystem', *a, **k):
        super().__init__(name, *a, **k)
        self.register_slot(self.song, self._on_scale_changed, "scale_name")
        self.register_slot(self.song, self._on_scale_intervals_changed, "scale_intervals")

    def _on_scale_changed(self):
        pass

    def _on_scale_intervals_changed(self):
        pass
