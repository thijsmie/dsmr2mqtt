"""
Unit parser for Home Assistant MQTT discovery

This module provides proper unit parsing and normalization for Home Assistant
device classes using the pint library for robust unit handling.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from typing import Optional, Tuple
import pint
from pint.errors import UndefinedUnitError, DefinitionSyntaxError

# Logging
import __main__
import logging
import os

script = os.path.basename(__main__.__file__)
script = os.path.splitext(script)[0]
logger = logging.getLogger(script + "." + __name__)

# Initialize pint unit registry
ureg = pint.UnitRegistry()

# Define mapping from unit dimensions to Home Assistant device classes
# Based on: https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
# Get the actual dimensionality strings from pint
ENERGY_DIMENSION = str(ureg.parse_expression("Wh").dimensionality)  # [mass] * [length] ** 2 / [time] ** 2
POWER_DIMENSION = str(ureg.parse_expression("W").dimensionality)  # [mass] * [length] ** 2 / [time] ** 3
VOLTAGE_DIMENSION = str(ureg.parse_expression("V").dimensionality)  # [mass] * [length] ** 2 / [time] ** 3 / [current]
CURRENT_DIMENSION = str(ureg.parse_expression("A").dimensionality)  # [current]
VOLUME_DIMENSION = str(ureg.parse_expression("m**3").dimensionality)  # [length] ** 3

DIMENSION_TO_DEVICE_CLASS = {
    ENERGY_DIMENSION: "energy",
    POWER_DIMENSION: "power",
    CURRENT_DIMENSION: "current",
    VOLTAGE_DIMENSION: "voltage",
    VOLUME_DIMENSION: "gas",
}

# Define state class based on device class
# "total" for cumulative values, "measurement" for instantaneous values
DEVICE_CLASS_STATE_CLASS = {
    "energy": "total",
    "gas": "total",
    "power": "measurement",
    "current": "measurement",
    "voltage": "measurement",
    "frequency": "measurement",
    "temperature": "measurement",
    "density": "measurement",
    "speed": "measurement",
    "mass_flow": "measurement",
    "volume_flow": "measurement",
}

# Mapping of Home Assistant preferred units for each device class
HA_PREFERRED_UNITS = {
    "energy": ["Wh", "kWh", "MWh", "GWh"],
    "power": ["W", "kW"],
    "current": ["A"],
    "voltage": ["V"],
    "gas": ["m³", "m3"],
    "frequency": ["Hz"],
    "temperature": ["°C", "K"],
}


def parse_unit(unit_str: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Parse a unit string and determine the appropriate Home Assistant device class.
    
    Args:
        unit_str: The unit string to parse (e.g., "W", "kWh", "Watt", "m3")
    
    Returns:
        Tuple of (device_class, state_class, normalized_unit):
            - device_class: HA device class (e.g., "power", "energy") or None
            - state_class: HA state class (e.g., "measurement", "total") or None  
            - normalized_unit: Normalized unit string suitable for HA
    """
    if not unit_str:
        return None, None, ""
    
    try:
        # Handle special cases for non-standard unit names
        # pint understands 'watt' in lowercase
        normalized_input = unit_str.lower() if unit_str.lower() == "watt" else unit_str
        
        # Parse the unit
        try:
            unit = ureg.parse_expression(normalized_input)
        except (UndefinedUnitError, DefinitionSyntaxError):
            # Try common alternatives
            if unit_str in ["m3", "m³"]:
                unit = ureg.parse_expression("meter**3")
            else:
                logger.debug(f"Could not parse unit: {unit_str}")
                return None, None, unit_str
        
        # Get the dimensionality
        dimensionality = str(unit.dimensionality)
        
        # Map to device class
        device_class = DIMENSION_TO_DEVICE_CLASS.get(dimensionality)
        
        if device_class is None:
            logger.debug(f"Unknown dimensionality for unit {unit_str}: {dimensionality}")
            return None, None, unit_str
        
        # Get state class
        state_class = DEVICE_CLASS_STATE_CLASS.get(device_class)
        
        # Normalize the unit to HA preferred format
        normalized_unit = _normalize_unit_for_ha(unit_str, normalized_input, device_class)
        
        return device_class, state_class, normalized_unit
        
    except Exception as e:
        logger.debug(f"Error parsing unit {unit_str}: {e}")
        return None, None, unit_str


def _normalize_unit_for_ha(original: str, parsed_str: str, device_class: str) -> str:
    """
    Normalize a unit to Home Assistant's preferred format.
    
    Args:
        original: Original unit string
        parsed_str: String used for parsing (may differ from original)
        device_class: The HA device class
    
    Returns:
        Normalized unit string
    """
    # Special handling for specific cases
    if device_class == "gas":
        # HA prefers m³ for gas volume
        if original in ["m3", "m³"]:
            return "m³"
    
    # For non-standard names, use the parsed version
    if original.lower() == "watt":
        return "W"
    
    # For most cases, keep the original if it's in the preferred list
    preferred = HA_PREFERRED_UNITS.get(device_class, [])
    if original in preferred:
        return original
    
    # Otherwise use what was parsed/normalized
    return parsed_str
