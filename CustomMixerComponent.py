from ableton.v3.control_surface.components import (
    MixerComponent,
    ScrollComponent,
    Scrollable
)

from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    TouchControl,
    MappedControl,
    SendValueInputControl,
    SendValueEncoderControl,
    control_matrix
)

from ableton.v2.control_surface.control import (
    MatrixControl
)

from ableton.v2.control_surface import (
    WrappingParameter
)
from ableton.v3.control_surface import ScriptForwarding

from ableton.v3.base import (
    listens,
    listenable_property,
)

from .Logger import logger

class CustomMixerComponent(MixerComponent):
    def __init__(self, name = "Mixer", *a, **k):
        super().__init__(name, *a, **k)

    