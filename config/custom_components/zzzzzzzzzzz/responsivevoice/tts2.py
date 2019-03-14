"""Support for the ResponsiveVoice service."""
# import asyncio
import logging
from http.client import HTTPException
# import re

# import aiohttp
# from aiohttp.hdrs import REFERER, USER_AGENT
# import async_timeout
import voluptuous as vol
# import yarl

from homeassistant.components.tts import CONF_LANG, PLATFORM_SCHEMA, Provider
# from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

# REQUIREMENTS = ['ResponsiveVoice', 'mpg123']
REQUIREMENTS = ['ResponsiveVoice']

_LOGGER = logging.getLogger(__name__)

CONF_GENDER = 'gender'
CONF_RATE = 'rate'
CONF_PITCH = 'pitch'
CONF_VOLUME = 'volume'

SUPPORT_LANGUAGES = [
    'UK English', 'US English', 'Arabic', 'Armenian', 'Australian',
    'Brazilian Portuguese', 'Chinese', 'Chinese (Hong Kong)',
    'Chinese Taiwan ', 'Czech', 'Danish', 'Deutsch', 'Dutch', 'Finnish',
    'French', 'Greek', 'Hindi', 'Hungarian', 'Indonesian', 'Italian',
    'Japanese', 'Korean', 'Latin', 'Norwegian', 'Polish', 'Portuguese',
    'Romanian', 'Russian', 'Slovak', 'Spanish', 'Spanish Latin American',
    'Swedish', 'Tamil', 'Thai', 'Turkish', 'Vietnamese', 'Afrikaans',
    'Albanian', 'Bosnian', 'Catalan', 'Croatian', 'Esperanto', 'Icelandic',
    'Latvian', 'Macedonian', 'Moldavian', 'Montenegrin', 'Serbian',
    'Serbo-Croatian', 'Swahili', 'Welsh'
]

SUPPORT_GENDER = [
    'Female', 'Male'
]

DEFAULT_LANG = 'Fallback UK'
DEFAULT_GENDER = 'Female'
DEFAULT_RATE = 0.5
DEFAULT_PITCH = 0.5
DEFAULT_VOLUME = 1

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORT_LANGUAGES),
    vol.Optional(CONF_GENDER, default=DEFAULT_GENDER): vol.In(SUPPORT_GENDER),
})


# async def async_get_engine(hass, config):
def get_engine(hass, config):
    """Set up ResponsiveVoice component."""
    return ResponsiveVoiceProvider(hass, config)


class ResponsiveVoiceProvider(Provider):
    """The ResponsiveVoice API provider."""

    def __init__(self, hass, conf):
        """Init ResponsiveVoice TTS service."""
        self.hass = hass
        self._lang = conf.get(CONF_LANG)
        self._gender = conf.get(CONF_GENDER)
        self.name = 'ResponsiveVoice'

    @property
    def default_language(self):
        """Return the default language."""
        return self._lang

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return SUPPORT_LANGUAGES

    # async def async_get_tts_audio(self, message, language, options=None):
    def get_tts_audio(self, message, language, options=None):
        """Load TTS from ResponsiveVoice."""
        if language is None:
            language = self._lang
        from responsive_voice import ResponsiveVoice

        # websession = async_get_clientsession(self.hass)
        try:
            engine = ResponsiveVoice()
            _LOGGER.error(message)
            data = engine.say(
                    sentence=message, gender=self._gender, lang=self._lang
                    )

        except HTTPException as ex:
            _LOGGER.error("Timeout for ResponsiveVoice speech")
            return None, None
        # try:
        #     with async_timeout.timeout(10, loop=self.hass.loop):
        #         engine = ResponsiveVoice()
        #         _LOGGER.error(message)
        #         data = engine.say(
        #             sentence=message, gender="self._gender", lang="self._lang"
        #             )

        #         if request.status != 200:
        #             _LOGGER.error("Error %d on load URL %s",
        #                           request.status, request.url)
        #             return None, None
        #         data += await request.read()

        # except (asyncio.TimeoutError, aiohttp.ClientError):
        #     _LOGGER.error("Timeout for ResponsiveVoice speech")
        #     return None, None
        return ('mp3', data)