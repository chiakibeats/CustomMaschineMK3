from ableton.v3.control_surface import (
    ControlSurface,
    ControlSurfaceSpecification
)

from ableton.v3.control_surface.component import (
    Component
)

from ableton.v3.control_surface.capabilities import (
    CONTROLLER_ID_KEY,
    HIDDEN, NOTES_CC,
    PORTS_KEY,
    SCRIPT,
    SYNC,
    REMOTE,
    controller_id,
    inport,
    outport)

from .Logger import logger
from .CustomMaschineMK3 import CustomMaschineMK3

def get_capabilities():
    return {
        CONTROLLER_ID_KEY: (
            controller_id(
                vendor_id = 0x17CC,
                product_ids = [0x1600],
                model_name = ["Maschine MK3"])),
        PORTS_KEY: [
            inport(port_name = "Maschine MK3 EXT In", props = [NOTES_CC, SYNC]),
            inport(port_name = "Maschine MK3 Ctrl In", props = [NOTES_CC, SCRIPT, HIDDEN]),
            outport(port_name = "Maschine MK3 EXT Out", props = [NOTES_CC, SYNC]),
            outport(port_name = "Maschine MK3 Ctrl Out", props = [NOTES_CC, SCRIPT, HIDDEN])]}

def create_instance(c_instance):
    logger.info("Create instance")
    return CustomMaschineMK3(c_instance = c_instance)
