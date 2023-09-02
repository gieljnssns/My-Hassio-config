"""
This component provides support for Home Automation Manager (HAM).
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/edgeos/
"""
import sys
import logging
import aiohttp
import asyncio

from .const import *

REQUIREMENTS = ['aiohttp']

_LOGGER = logging.getLogger(__name__)


class EdgeOSWebAPI:
    def __init__(self, edgeos_url, hass_loop):
        self._last_update = datetime.now()
        self._session = None

        self._last_valid = EMPTY_LAST_VALID
        self._edgeos_url = edgeos_url
        self._hass_loop = hass_loop

    def initialize(self, cookies):
        self.close()

        self._session = aiohttp.ClientSession(cookies=cookies, loop=self._hass_loop)

    def close(self):
        if self.is_initialized:
            yield from self._session.close()

    @property
    def is_initialized(self):
        return self._session is not None and not self._session.closed

    async def async_get(self, url):
        async with self._session.get(url, ssl=False) as response:
            response.raise_for_status()

            result = await response.json()

            self._last_update = datetime.now()

            return result

    @property
    def last_update(self):
        result = self._last_update

        return result

    @asyncio.coroutine
    def heartbeat(self, max_age=HEARTBEAT_MAX_AGE):
        try:
            if self.is_initialized:
                ts = datetime.now()
                current_invocation = datetime.now() - self._last_valid
                if current_invocation > timedelta(seconds=max_age):
                    current_ts = str(int(ts.timestamp()))

                    heartbeat_req_url = self.get_edgeos_api_endpoint(EDGEOS_API_HEARTBREAT)
                    heartbeat_req_full_url = API_URL_HEARTBEAT_TEMPLATE.format(heartbeat_req_url, current_ts)

                    response = yield from self.async_get(heartbeat_req_full_url)

                    _LOGGER.debug(f'Heartbeat response: {response}')

                    self._last_valid = ts
            else:
                _LOGGER.warning(f'Heartbeat not ran due to closed session')
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to perform heartbeat, Error: {ex}, Line: {line_number}')

    @asyncio.coroutine
    def get_devices_data(self):
        result = None

        try:
            if self.is_initialized:
                get_req_url = self.get_edgeos_api_endpoint(EDGEOS_API_GET)

                result_json = yield from self.async_get(get_req_url)

                if RESPONSE_SUCCESS_KEY in result_json:
                    success_key = str(result_json.get(RESPONSE_SUCCESS_KEY, '')).lower()

                    if success_key == TRUE_STR:
                        if EDGEOS_API_GET.upper() in result_json:
                            result = result_json.get(EDGEOS_API_GET.upper(), {})
                    else:
                        error_message = result_json[RESPONSE_ERROR_KEY]
                        _LOGGER.error(f'Failed, Error: {error_message}')
                else:
                    _LOGGER.error('Invalid response, not contain success status')
            else:
                _LOGGER.warning(f'Get devices data not ran due to closed session')
        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to get devices data, Error: {ex}, Line: {line_number}')

        return result

    @asyncio.coroutine
    def get_general_data(self, item):
        result = None

        try:
            if self.is_initialized:
                clean_item = item.replace(STRING_DASH, STRING_UNDERSCORE)
                data_req_url = self.get_edgeos_api_endpoint(EDGEOS_API_DATA)
                data_req_full_url = API_URL_DATA_TEMPLATE.format(data_req_url, clean_item)

                data = yield from self.async_get(data_req_full_url)

                if str(data.get(RESPONSE_SUCCESS_KEY, EMPTY_STRING)) == RESPONSE_FAILURE_CODE:
                    error = data.get(RESPONSE_ERROR_KEY, EMPTY_STRING)

                    _LOGGER.error(f'Failed to load {item}, Reason: {error}')
                    result = None
                else:
                    result = data.get(RESPONSE_OUTPUT)
            else:
                _LOGGER.warning(f'Get general data not ran due to closed session')

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f'Failed to load {item}, Error: {ex}, Line: {line_number}')
            result = None

        return result

    def get_edgeos_api_endpoint(self, controller):
        url = EDGEOS_API_URL.format(self._edgeos_url, controller)

        return url
