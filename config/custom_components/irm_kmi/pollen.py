"""Parse pollen info from SVG from IRM KMI api"""
import logging
import xml.etree.ElementTree as ET
from typing import List

from custom_components.irm_kmi.const import POLLEN_LEVEL_TO_COLOR, POLLEN_NAMES

_LOGGER = logging.getLogger(__name__)


class PollenParser:
    """
    Extract pollen level from an SVG provided by the IRM KMI API.
    To get the data, match pollen names and pollen levels that are vertically aligned.  Then, map the value to the
    corresponding color on the scale.
    """

    def __init__(
            self,
            xml_string: str
    ):
        self._xml = xml_string

    @staticmethod
    def get_default_data() -> dict:
        """Return all the known pollen with 'none' value"""
        return {k.lower(): 'none' for k in POLLEN_NAMES}

    @staticmethod
    def get_unavailable_data() -> dict:
        """Return all the known pollen with 'none' value"""
        return {k.lower(): None for k in POLLEN_NAMES}

    @staticmethod
    def get_option_values() -> List[str]:
        """List all the values that the pollen can have"""
        return list(POLLEN_LEVEL_TO_COLOR.values()) + ['none']

    @staticmethod
    def _extract_elements(root) -> List[ET.Element]:
        """Recursively collect all elements of the SVG in a list"""
        elements = []
        for child in root:
            elements.append(child)
            elements.extend(PollenParser._extract_elements(child))
        return elements

    @staticmethod
    def _get_elem_text(e) -> str | None:
        if e.text is not None:
            return e.text.strip()
        return None

    def get_pollen_data(self) -> dict:
        """From the XML string, parse the SVG and extract the pollen data from the image.
        If an error occurs, return the default value"""
        pollen_data = self.get_default_data()
        try:
            _LOGGER.debug(f"Full SVG: {self._xml}")
            root = ET.fromstring(self._xml)
        except ET.ParseError:
            _LOGGER.warning("Could not parse SVG pollen XML")
            return pollen_data

        elements: List[ET.Element] = self._extract_elements(root)

        pollens = {e.attrib.get('x', None): self._get_elem_text(e).lower()
                   for e in elements if 'tspan' in e.tag and self._get_elem_text(e) in POLLEN_NAMES}

        pollen_levels = {e.attrib.get('x', None): POLLEN_LEVEL_TO_COLOR[self._get_elem_text(e)]
                         for e in elements if 'tspan' in e.tag and self._get_elem_text(e) in POLLEN_LEVEL_TO_COLOR}

        for position, pollen in pollens.items():
            if position is not None and position in pollen_levels:
                pollen_data[pollen] = pollen_levels[position]

        _LOGGER.debug(f"Pollen data: {pollen_data}")
        return pollen_data
