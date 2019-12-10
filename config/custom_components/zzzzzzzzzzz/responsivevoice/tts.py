"""Support for ResponsiveVoice speech service."""
import logging

from responsive_voice import ResponsiveVoice
import voluptuous as vol

from homeassistant.components.tts import CONF_LANG, PLATFORM_SCHEMA, Provider
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# SUPPORTED_LANGUAGES = ["en-GB", "en-AU", "en-US", "en-ZA", "en-IE", "he-IL", "th-TH",
#     "pt-BR", "pt-PT", "sk-SK", "fr-CA", "ro-RO", "no-NO", "fi-FI", "pl-PL", "de-DE", 
#     "nl-NL", "id-ID", "tr-TR", "it-IT", "fr-FR", "ru-RU", "es-MX", "es-ES", "zh-HK", 
#     "zh-TW", "zh-CN", "sv-SE", "hu-HU", "nl-BE", "ar-SA", "ko-KR", "cs-CZ", "da-DK", 
#     "hi-IN", "el-GR", "ja-JP"]

SUPPORTED_LANGUAGES = ["ENGLISH_GB","ENGLISH_AU", "ENGLISH_US", "ENGLISH_ZA",
    "ENGLISH_IE", "HEBREW", "THAI", "PORTUGESE_BR", "PORTUGESE_PT", "SLOVAK",
    "FRENCH_CA", "ROMANIAN", "NORWEGIAN", "FINNISH", "POLISH", "GERMAN",
    "DUTCH", "INDONESIAN", "TURKISH", "ITALIAN", "FRENCH", "RUSSIAN",
    "SPANISH_MX", "SPANISH_ES", "CHINESE_HK", "CHINESE_TW", "CHINESE_CN",
    "SWEDISH", "HUNGARIAN", "DUTCH_BE", "ARABIC_SA", "KOREAN", "CZECH",
    "DANISH", "HINDI", "GREEK", "JAPANESE"]

DEFAULT_LANG = "ENGLISH_US"

CONF_SPEED = "speed"
CONF_PITCH = "pitch"
CONF_VOLUME = "volume"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_LANG, default=DEFAULT_LANG): vol.In(SUPPORTED_LANGUAGES),
        vol.Optional(CONF_SPEED, default=0.5): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=1)
        ),
        vol.Optional(CONF_PITCH, default=0.5): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=1)
        ),
        vol.Optional(CONF_VOLUME, default=1): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=1)
        ),
    }
)

# Keys are options in the config file, and Values are options
# required by Baidu TTS API.
_OPTIONS = {
    CONF_PITCH: "pit",
    CONF_SPEED: "spd",
    CONF_VOLUME: "vol",
}
SUPPORTED_OPTIONS = [CONF_PITCH, CONF_SPEED, CONF_VOLUME]


def get_engine(hass, config, discovery_info=None):
    """Set up ResponsiveVoice TTS component."""
    return ResponsiveVoiceTTSProvider(hass, config)


class ResponsiveVoiceTTSProvider(Provider):
    """ResponsiveVoice TTS speech api provider."""

    def __init__(self, hass, conf):
        """Init ResponsiveVoice TTS service."""
        self.hass = hass
        self._lang = conf.get(CONF_LANG)
        self._codec = "mp3"
        self.name = "ResponsiveVoiceTTS"
        self._speed = float(conf.get(CONF_SPEED))
        self._pitch = float(conf.get(CONF_PITCH))
        self._volume = float(conf.get(CONF_VOLUME))

        # self._speech_conf_data = {
        #     _OPTIONS[CONF_PITCH]: conf.get(CONF_PITCH),
        #     _OPTIONS[CONF_SPEED]: conf.get(CONF_SPEED),
        #     _OPTIONS[CONF_VOLUME]: conf.get(CONF_VOLUME),
        # }

        # self._form_data = {
        #     "hl": conf[CONF_LANG],
        #     "c": (conf[CONF_CODEC]).upper(),
        #     "f": conf[CONF_FORMAT],
        # }

    @property
    def default_language(self):
        """Return the default language."""
        return self._lang

    @property
    def supported_languages(self):
        """Return a list of supported languages."""
        return SUPPORTED_LANGUAGES

    # @property
    # def default_options(self):
    #     """Return a dict including default options."""
    #     return {
    #         CONF_PITCH: self._speech_conf_data[_OPTIONS[CONF_PITCH]],
    #         CONF_SPEED: self._speech_conf_data[_OPTIONS[CONF_SPEED]],
    #         CONF_VOLUME: self._speech_conf_data[_OPTIONS[CONF_VOLUME]],
    #     }

    @property
    def supported_options(self):
        """Return a list of supported options."""
        return SUPPORTED_OPTIONS

    def get_tts_audio(self, message, language, options=None):
        """Load TTS from ResponsiveVoiceTTS."""

        engine = ResponsiveVoice()
        # from responsive_voice.voices import Ellen

        # ellen = Ellen()

        # result = ellen.say(message)
        print("message", message, "language", language, "pitch", self._pitch,
              "rate", self._speed, "vol", self._volume)

        result = engine.say(message, language, pitch=self._pitch,
                            rate=self._speed, vol=self._volume)
        
        # result = engine.get_mp3(message, language, pitch=self._pitch,
        #                         rate=self._speed, vol=self._volume)

        # if options is None:
        #     result = engine.say(message, lang=language, pitch=self._pitch,
        #                         rate=self._speed, vol=self._volume)
        # else:
        #     speech_data = self._speech_conf_data.copy()
        #     for key, value in options.items():
        #         speech_data[_OPTIONS[key]] = value

        #     result = engine.say(message, language, 1, speech_data)
        
        print(result)

        if isinstance(result, dict):
            _LOGGER.error(
                "ResponsiveVoice TTS error-- err_no:%d; err_msg:%s; err_detail:%s",
                result["err_no"],
                result["err_msg"],
                result["err_detail"],
            )
            return None, None

        return self._codec, result
