# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

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

from custom_maschine.logger import logger
from custom_maschine.control_surface import CustomMaschineBase
from custom_maschine.settings import SettingsRepository
from custom_maschine.util import SETTINGS_FILE_NAME
from .specification import CustomMaschineMikroMK3Spec, init_specification, SCHEMA

def get_capabilities():
    return {
        CONTROLLER_ID_KEY: (
            controller_id(
                vendor_id = 0x17CC,
                product_ids = [0x1700],
                model_name = ["Maschine Mikro MK3"])),
        PORTS_KEY: [
            inport(props = [NOTES_CC, SCRIPT, REMOTE, HIDDEN]),
            outport(props = [NOTES_CC, SCRIPT, REMOTE, HIDDEN])],
    }

def create_instance(c_instance):
    logger.info("Create instance")
    settings = SettingsRepository(SETTINGS_FILE_NAME, SCHEMA)
    init_specification(settings)
    return CustomMaschineBase(specification = CustomMaschineMikroMK3Spec, c_instance = c_instance)
