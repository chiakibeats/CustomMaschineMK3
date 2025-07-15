# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

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
    outport
)

from .Logger import logger
from .CustomMaschineMK3 import CustomMaschineMK3

def get_capabilities():
    return {
        CONTROLLER_ID_KEY: (
            controller_id(
                vendor_id = 0x17CC,
                product_ids = [0x1600, 0x1820],
                model_name = ["Maschine MK3", "Maschine Plus"])),
        PORTS_KEY: [
            inport(props = [NOTES_CC, SYNC]),
            inport(props = [NOTES_CC, SCRIPT, REMOTE, HIDDEN]),
            outport(props = [NOTES_CC, SYNC]),
            outport(props = [NOTES_CC, SCRIPT, REMOTE, HIDDEN])],
    }

def create_instance(c_instance):
    logger.info("Create instance")
    return CustomMaschineMK3(c_instance = c_instance)
