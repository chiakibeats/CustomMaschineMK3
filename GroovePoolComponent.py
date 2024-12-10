from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import StepEncoderControl
from .Logger import logger
from ableton.v3.base import clamp, sign

class GroovePoolComponent(Component, Renderable):
    coarse_groove_amount = StepEncoderControl(num_steps = 64)
    fine_groove_amount = StepEncoderControl(num_steps = 64)

    def __init__(self, name = "Groove_Pool", *a, **k):
        super().__init__(name, *a, **k)
        self.coarse_groove_amount.connect_property(
            self.song,
            "groove_amount",
            transform = lambda x: clamp(self.song.groove_amount + sign(x) / 20, 0, 1.3))
        
        self.fine_groove_amount.connect_property(
            self.song,
            "groove_amount",
            transform = lambda x: clamp(self.song.groove_amount + sign(x) / 100, 0, 1.3))



