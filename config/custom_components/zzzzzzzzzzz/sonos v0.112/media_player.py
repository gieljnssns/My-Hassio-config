"""Support to interface with Sonos players."""
import asyncio
import datetime
import functools as ft
import logging
import socket

import async_timeout
import pysonos
from pysonos import alarms
from pysonos.exceptions import SoCoException, SoCoUPnPException
import pysonos.music_library
import pysonos.snapshot
import voluptuous as vol

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_ENQUEUE,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_PLAYLIST,
    SUPPORT_CLEAR_PLAYLIST,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SEEK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_SHUFFLE_SET,
    SUPPORT_STOP,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
)
from homeassistant.const import (
    ATTR_TIME,
    EVENT_HOMEASSISTANT_STOP,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import ServiceCall, callback
from homeassistant.helpers import config_validation as cv, entity_platform, service
import homeassistant.helpers.device_registry as dr
from homeassistant.util.dt import utcnow

from . import (
    CONF_ADVERTISE_ADDR,
    CONF_HOSTS,
    CONF_INTERFACE_ADDR,
    DOMAIN as SONOS_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 10
DISCOVERY_INTERVAL = 60

SUPPORT_SONOS = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_PLAY
    | SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_SEEK
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_SHUFFLE_SET
    | SUPPORT_CLEAR_PLAYLIST
)

DATA_SONOS = "sonos_media_player"

SOURCE_LINEIN = "Line-in"
SOURCE_TV = "TV"

ATTR_SONOS_GROUP = "sonos_group"

UPNP_ERRORS_TO_IGNORE = ["701", "711", "712"]

SERVICE_JOIN = "join"
SERVICE_UNJOIN = "unjoin"
SERVICE_SNAPSHOT = "snapshot"
SERVICE_RESTORE = "restore"
SERVICE_SET_TIMER = "set_sleep_timer"
SERVICE_CLEAR_TIMER = "clear_sleep_timer"
SERVICE_UPDATE_ALARM = "update_alarm"
SERVICE_SET_OPTION = "set_option"
SERVICE_PLAY_QUEUE = "play_queue"
SERVICE_REMOVE_FROM_QUEUE = "remove_from_queue"

ATTR_SLEEP_TIME = "sleep_time"
ATTR_ALARM_ID = "alarm_id"
ATTR_VOLUME = "volume"
ATTR_ENABLED = "enabled"
ATTR_INCLUDE_LINKED_ZONES = "include_linked_zones"
ATTR_MASTER = "master"
ATTR_WITH_GROUP = "with_group"
ATTR_NIGHT_SOUND = "night_sound"
ATTR_SPEECH_ENHANCE = "speech_enhance"
ATTR_QUEUE_POSITION = "queue_position"

UNAVAILABLE_VALUES = {"", "NOT_IMPLEMENTED", None}


class SonosData:
    """Storage class for platform global data."""

    def __init__(self):
        """Initialize the data."""
        self.entities = []
        self.discovered = []
        self.topology_condition = asyncio.Condition()
        self.discovery_thread = None
        self.hosts_heartbeat = None


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Sonos platform. Obsolete."""
    _LOGGER.error(
        "Loading Sonos by media_player platform configuration is no longer supported"
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Sonos from a config entry."""
    if DATA_SONOS not in hass.data:
        hass.data[DATA_SONOS] = SonosData()

    config = hass.data[SONOS_DOMAIN].get("media_player", {})
    _LOGGER.debug("Reached async_setup_entry, config=%s", config)

    advertise_addr = config.get(CONF_ADVERTISE_ADDR)
    if advertise_addr:
        pysonos.config.EVENT_ADVERTISE_IP = advertise_addr

    def _stop_discovery(event):
        data = hass.data[DATA_SONOS]
        if data.discovery_thread:
            data.discovery_thread.stop()
            data.discovery_thread = None
        if data.hosts_heartbeat:
            data.hosts_heartbeat()
            data.hosts_heartbeat = None

    def _discovery(now=None):
        """Discover players from network or configuration."""
        hosts = config.get(CONF_HOSTS)

        def _discovered_player(soco):
            """Handle a (re)discovered player."""
            try:
                _LOGGER.debug("Reached _discovered_player, soco=%s", soco)

                if soco.uid not in hass.data[DATA_SONOS].discovered:
                    _LOGGER.debug("Adding new entity")
                    hass.data[DATA_SONOS].discovered.append(soco.uid)
                    hass.add_job(async_add_entities, [SonosEntity(soco)])
                else:
                    entity = _get_entity_from_soco_uid(hass, soco.uid)
                    if entity and (entity.soco == soco or not entity.available):
                        _LOGGER.debug("Seen %s", entity)
                        hass.add_job(entity.async_seen(soco))

            except SoCoException as ex:
                _LOGGER.debug("SoCoException, ex=%s", ex)

        if hosts:
            for host in hosts:
                try:
                    _LOGGER.debug("Testing %s", host)
                    player = pysonos.SoCo(socket.gethostbyname(host))
                    if player.is_visible:
                        # Make sure that the player is available
                        _ = player.volume

                        _discovered_player(player)
                except (OSError, SoCoException) as ex:
                    _LOGGER.debug("Exception %s", ex)
                    if now is None:
                        _LOGGER.warning("Failed to initialize '%s'", host)

            _LOGGER.debug("Tested all hosts")
            hass.data[DATA_SONOS].hosts_heartbeat = hass.helpers.event.call_later(
                DISCOVERY_INTERVAL, _discovery
            )
        else:
            _LOGGER.debug("Starting discovery thread")
            hass.data[DATA_SONOS].discovery_thread = pysonos.discover_thread(
                _discovered_player,
                interval=DISCOVERY_INTERVAL,
                interface_addr=config.get(CONF_INTERFACE_ADDR),
            )

    _LOGGER.debug("Adding discovery job")
    hass.async_add_executor_job(_discovery)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _stop_discovery)

    platform = entity_platform.current_platform.get()

    @service.verify_domain_control(hass, SONOS_DOMAIN)
    async def async_service_handle(service_call: ServiceCall):
        """Handle dispatched services."""
        entities = await platform.async_extract_from_service(service_call)

        if not entities:
            return

        if service_call.service == SERVICE_JOIN:
            master = platform.entities.get(service_call.data[ATTR_MASTER])
            if master:
                await SonosEntity.join_multi(hass, master, entities)
            else:
                _LOGGER.error(
                    "Invalid master specified for join service: %s",
                    service_call.data[ATTR_MASTER],
                )
        elif service_call.service == SERVICE_UNJOIN:
            await SonosEntity.unjoin_multi(hass, entities)
        elif service_call.service == SERVICE_SNAPSHOT:
            await SonosEntity.snapshot_multi(
                hass, entities, service_call.data[ATTR_WITH_GROUP]
            )
        elif service_call.service == SERVICE_RESTORE:
            await SonosEntity.restore_multi(
                hass, entities, service_call.data[ATTR_WITH_GROUP]
            )

    hass.services.async_register(
        SONOS_DOMAIN,
        SERVICE_JOIN,
        async_service_handle,
        cv.make_entity_service_schema({vol.Required(ATTR_MASTER): cv.entity_id}),
    )

    hass.services.async_register(
        SONOS_DOMAIN,
        SERVICE_UNJOIN,
        async_service_handle,
        cv.make_entity_service_schema({}),
    )

    join_unjoin_schema = cv.make_entity_service_schema(
        {vol.Optional(ATTR_WITH_GROUP, default=True): cv.boolean}
    )

    hass.services.async_register(
        SONOS_DOMAIN, SERVICE_SNAPSHOT, async_service_handle, join_unjoin_schema
    )

    hass.services.async_register(
        SONOS_DOMAIN, SERVICE_RESTORE, async_service_handle, join_unjoin_schema
    )

    platform.async_register_entity_service(
        SERVICE_SET_TIMER,
        {
            vol.Required(ATTR_SLEEP_TIME): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=86399)
            )
        },
        "set_sleep_timer",
    )

    platform.async_register_entity_service(SERVICE_CLEAR_TIMER, {}, "clear_sleep_timer")

    platform.async_register_entity_service(
        SERVICE_UPDATE_ALARM,
        {
            vol.Required(ATTR_ALARM_ID): cv.positive_int,
            vol.Optional(ATTR_TIME): cv.time,
            vol.Optional(ATTR_VOLUME): cv.small_float,
            vol.Optional(ATTR_ENABLED): cv.boolean,
            vol.Optional(ATTR_INCLUDE_LINKED_ZONES): cv.boolean,
        },
        "set_alarm",
    )

    platform.async_register_entity_service(
        SERVICE_SET_OPTION,
        {
            vol.Optional(ATTR_NIGHT_SOUND): cv.boolean,
            vol.Optional(ATTR_SPEECH_ENHANCE): cv.boolean,
        },
        "set_option",
    )

    platform.async_register_entity_service(
        SERVICE_PLAY_QUEUE,
        {vol.Optional(ATTR_QUEUE_POSITION): cv.positive_int},
        "play_queue",
    )

    platform.async_register_entity_service(
        SERVICE_REMOVE_FROM_QUEUE,
        {vol.Optional(ATTR_QUEUE_POSITION): cv.positive_int},
        "remove_from_queue",
    )


class _ProcessSonosEventQueue:
    """Queue like object for dispatching sonos events."""

    def __init__(self, handler):
        """Initialize Sonos event queue."""
        self._handler = handler

    def put(self, item, block=True, timeout=None):
        """Process event."""
        try:
            self._handler(item)
        except SoCoException as ex:
            _LOGGER.warning("Error calling %s: %s", self._handler, ex)


def _get_entity_from_soco_uid(hass, uid):
    """Return SonosEntity from SoCo uid."""
    for entity in hass.data[DATA_SONOS].entities:
        if uid == entity.unique_id:
            return entity
    return None


def soco_error(errorcodes=None):
    """Filter out specified UPnP errors from logs and avoid exceptions."""

    def decorator(funct):
        """Decorate functions."""

        @ft.wraps(funct)
        def wrapper(*args, **kwargs):
            """Wrap for all soco UPnP exception."""
            try:
                return funct(*args, **kwargs)
            except SoCoUPnPException as err:
                if not errorcodes or err.error_code not in errorcodes:
                    _LOGGER.error("Error on %s with %s", funct.__name__, err)
            except SoCoException as err:
                _LOGGER.error("Error on %s with %s", funct.__name__, err)

        return wrapper

    return decorator


def soco_coordinator(funct):
    """Call function on coordinator."""

    @ft.wraps(funct)
    def wrapper(entity, *args, **kwargs):
        """Wrap for call to coordinator."""
        if entity.is_coordinator:
            return funct(entity, *args, **kwargs)
        return funct(entity.coordinator, *args, **kwargs)

    return wrapper


def _timespan_secs(timespan):
    """Parse a time-span into number of seconds."""
    if timespan in UNAVAILABLE_VALUES:
        return None

    return sum(60 ** x[0] * int(x[1]) for x in enumerate(reversed(timespan.split(":"))))


class SonosEntity(MediaPlayerEntity):
    """Representation of a Sonos entity."""

    def __init__(self, player):
        """Initialize the Sonos entity."""
        self._subscriptions = []
        self._poll_timer = None
        self._seen_timer = None
        self._volume_increment = 2
        self._unique_id = player.uid
        self._player = player
        self._player_volume = None
        self._player_muted = None
        self._shuffle = None
        self._coordinator = None
        self._sonos_group = [self]
        self._status = None
        self._uri = None
        self._media_duration = None
        self._media_position = None
        self._media_position_updated_at = None
        self._media_image_url = None
        self._media_artist = None
        self._media_album_name = None
        self._media_title = None
        self._is_playing_local_queue = None
        self._queue_position = None
        self._night_sound = None
        self._speech_enhance = None
        self._source_name = None
        self._favorites = []
        self._soco_snapshot = None
        self._snapshot_group = None

        # Set these early since device_info() needs them
        speaker_info = self.soco.get_speaker_info(True)
        self._name = speaker_info["zone_name"]
        self._model = speaker_info["model_name"]
        self._sw_version = speaker_info["software_version"]
        self._mac_address = speaker_info["mac_address"]

    async def async_added_to_hass(self):
        """Subscribe sonos events."""
        await self.async_seen(self.soco)

        self.hass.data[DATA_SONOS].entities.append(self)

        def _rebuild_groups():
            """Build the current group topology."""
            for entity in self.hass.data[DATA_SONOS].entities:
                entity.update_groups()

        self.hass.async_add_executor_job(_rebuild_groups)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    def __hash__(self):
        """Return a hash of self."""
        return hash(self.unique_id)

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(SONOS_DOMAIN, self._unique_id)},
            "name": self._name,
            "model": self._model.replace("Sonos ", ""),
            "sw_version": self._sw_version,
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._mac_address)},
            "manufacturer": "Sonos",
        }

    @property
    @soco_coordinator
    def state(self):
        """Return the state of the entity."""
        if self._status in ("PAUSED_PLAYBACK", "STOPPED",):
            # Sonos can consider itself "paused" but without having media loaded
            # (happens if playing Spotify and via Spotify app you pick another device to play on)
            if self.media_title is None:
                return STATE_IDLE
            return STATE_PAUSED
        if self._status in ("PLAYING", "TRANSITIONING"):
            return STATE_PLAYING
        return STATE_IDLE

    @property
    def is_coordinator(self):
        """Return true if player is a coordinator."""
        return self._coordinator is None

    @property
    def soco(self):
        """Return soco object."""
        return self._player

    @property
    def coordinator(self):
        """Return coordinator of this player."""
        return self._coordinator

    async def async_seen(self, player):
        """Record that this player was seen right now."""
        was_available = self.available

        self._player = player

        if self._seen_timer:
            self._seen_timer()

        self._seen_timer = self.hass.helpers.event.async_call_later(
            2.5 * DISCOVERY_INTERVAL, self.async_unseen
        )

        if was_available:
            return

        self._poll_timer = self.hass.helpers.event.async_track_time_interval(
            self.update, datetime.timedelta(seconds=SCAN_INTERVAL)
        )

        done = await self.hass.async_add_executor_job(self._attach_player)
        if not done:
            self._seen_timer()
            self.async_unseen()

        self.async_write_ha_state()

    @callback
    def async_unseen(self, now=None):
        """Make this player unavailable when it was not seen recently."""
        self._seen_timer = None

        if self._poll_timer:
            self._poll_timer()
            self._poll_timer = None

        def _unsub(subscriptions):
            for subscription in subscriptions:
                subscription.unsubscribe()

        self.hass.async_add_executor_job(_unsub, self._subscriptions)

        self._subscriptions = []

        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._seen_timer is not None

    def _clear_media_position(self):
        """Clear the media_position."""
        self._media_position = None
        self._media_position_updated_at = None

    def _set_favorites(self):
        """Set available favorites."""
        self._favorites = []
        for fav in self.soco.music_library.get_sonos_favorites():
            try:
                # Exclude non-playable favorites with no linked resources
                if fav.reference.resources:
                    self._favorites.append(fav)
            except SoCoException as ex:
                # Skip unknown types
                _LOGGER.error("Unhandled favorite '%s': %s", fav.title, ex)

    def _attach_player(self):
        """Get basic information and add event subscriptions."""
        try:
            self._shuffle = self.soco.shuffle
            self.update_volume()
            self._set_favorites()

            player = self.soco

            def subscribe(sonos_service, action):
                """Add a subscription to a pysonos service."""
                queue = _ProcessSonosEventQueue(action)
                sub = sonos_service.subscribe(auto_renew=True, event_queue=queue)
                self._subscriptions.append(sub)

            subscribe(player.avTransport, self.update_media)
            subscribe(player.renderingControl, self.update_volume)
            subscribe(player.zoneGroupTopology, self.update_groups)
            subscribe(player.contentDirectory, self.update_content)
            return True
        except SoCoException as ex:
            _LOGGER.warning("Could not connect %s: %s", self.entity_id, ex)
            return False

    @property
    def should_poll(self):
        """Return that we should not be polled (we handle that internally)."""
        return False

    def update(self, now=None):
        """Retrieve latest state."""
        try:
            self.update_groups()
            self.update_volume()
            if self.is_coordinator:
                self.update_media()
        except SoCoException:
            pass

    def update_media(self, event=None):
        """Update information about currently playing media."""
        transport_info = self.soco.get_current_transport_info()
        new_status = transport_info.get("current_transport_state")

        # Ignore transitions, we should get the target state soon
        if new_status == "TRANSITIONING":
            return

        self._shuffle = self.soco.shuffle
        self._uri = None
        self._media_duration = None
        self._media_image_url = None
        self._media_artist = None
        self._media_album_name = None
        self._media_title = None
        self._source_name = None

        update_position = new_status != self._status
        self._status = new_status

        self._is_playing_local_queue = self.soco.is_playing_local_queue

        if self.soco.is_playing_tv:
            self.update_media_linein(SOURCE_TV)
        elif self.soco.is_playing_line_in:
            self.update_media_linein(SOURCE_LINEIN)
        else:
            track_info = self.soco.get_current_track_info()
            if not track_info["uri"]:
                self._clear_media_position()
            else:
                self._uri = track_info["uri"]
                self._media_artist = track_info.get("artist")
                self._media_album_name = track_info.get("album")
                self._media_title = track_info.get("title")

                if self.soco.is_radio_uri(track_info["uri"]):
                    variables = event and event.variables
                    self.update_media_radio(variables, track_info)
                else:
                    self.update_media_music(update_position, track_info)

        self.schedule_update_ha_state()

        # Also update slaves
        for entity in self.hass.data[DATA_SONOS].entities:
            coordinator = entity.coordinator
            if coordinator and coordinator.unique_id == self.unique_id:
                entity.schedule_update_ha_state()

    def update_media_linein(self, source):
        """Update state when playing from line-in/tv."""
        self._clear_media_position()

        self._media_title = source
        self._source_name = source

    def update_media_radio(self, variables, track_info):
        """Update state when streaming radio."""
        self._clear_media_position()

        try:
            library = pysonos.music_library.MusicLibrary(self.soco)
            album_art_uri = variables["current_track_meta_data"].album_art_uri
            self._media_image_url = library.build_album_art_full_uri(album_art_uri)
        except (TypeError, KeyError, AttributeError):
            pass

        # Non-playing radios will not have a current title. Radios without tagging
        # can have part of the radio URI as title. In these cases we try to use the
        # radio name instead.
        try:
            uri_meta_data = variables["enqueued_transport_uri_meta_data"]
            if isinstance(
                uri_meta_data, pysonos.data_structures.DidlAudioBroadcast
            ) and (
                self.state != STATE_PLAYING
                or self.soco.is_radio_uri(self._media_title)
                or self._media_title in self._uri
            ):
                self._media_title = uri_meta_data.title
        except (TypeError, KeyError, AttributeError):
            pass

        # Check if currently playing radio station is in favorites
        media_info = self.soco.avTransport.GetMediaInfo([("InstanceID", 0)])
        for fav in self._favorites:
            if fav.reference.get_uri() == media_info["CurrentURI"]:
                self._source_name = fav.title

    def update_media_music(self, update_media_position, track_info):
        """Update state when playing music tracks."""
        self._media_duration = _timespan_secs(track_info.get("duration"))
        current_position = _timespan_secs(track_info.get("position"))

        # player started reporting position?
        if current_position is not None and self._media_position is None:
            update_media_position = True

        # position jumped?
        if current_position is not None and self._media_position is not None:
            if self.state == STATE_PLAYING:
                time_diff = utcnow() - self._media_position_updated_at
                time_diff = time_diff.total_seconds()
            else:
                time_diff = 0

            calculated_position = self._media_position + time_diff

            if abs(calculated_position - current_position) > 1.5:
                update_media_position = True

        if current_position is None:
            self._clear_media_position()
        elif update_media_position:
            self._media_position = current_position
            self._media_position_updated_at = utcnow()

        self._media_image_url = track_info.get("album_art")

        self._queue_position = int(track_info.get("playlist_position")) - 1

    def update_volume(self, event=None):
        """Update information about currently volume settings."""
        if event:
            variables = event.variables

            if "volume" in variables:
                self._player_volume = int(variables["volume"]["Master"])

            if "mute" in variables:
                self._player_muted = variables["mute"]["Master"] == "1"

            if "night_mode" in variables:
                self._night_sound = variables["night_mode"] == "1"

            if "dialog_level" in variables:
                self._speech_enhance = variables["dialog_level"] == "1"

            self.schedule_update_ha_state()
        else:
            self._player_volume = self.soco.volume
            self._player_muted = self.soco.mute
            self._night_sound = self.soco.night_mode
            self._speech_enhance = self.soco.dialog_mode

    def update_groups(self, event=None):
        """Handle callback for topology change event."""

        def _get_soco_group():
            """Ask SoCo cache for existing topology."""
            coordinator_uid = self.unique_id
            slave_uids = []

            try:
                if self.soco.group and self.soco.group.coordinator:
                    coordinator_uid = self.soco.group.coordinator.uid
                    slave_uids = [
                        p.uid
                        for p in self.soco.group.members
                        if p.uid != coordinator_uid
                    ]
            except SoCoException:
                pass

            return [coordinator_uid] + slave_uids

        async def _async_extract_group(event):
            """Extract group layout from a topology event."""
            group = event and event.zone_player_uui_ds_in_group
            if group:
                return group.split(",")

            return await self.hass.async_add_executor_job(_get_soco_group)

        @callback
        def _async_regroup(group):
            """Rebuild internal group layout."""
            sonos_group = []
            for uid in group:
                entity = _get_entity_from_soco_uid(self.hass, uid)
                if entity:
                    sonos_group.append(entity)

            self._coordinator = None
            self._sonos_group = sonos_group
            self.async_write_ha_state()

            for slave_uid in group[1:]:
                slave = _get_entity_from_soco_uid(self.hass, slave_uid)
                if slave:
                    # pylint: disable=protected-access
                    slave._coordinator = self
                    slave._sonos_group = sonos_group
                    slave.async_schedule_update_ha_state()

        async def _async_handle_group_event(event):
            """Get async lock and handle event."""
            if event and self._poll_timer:
                # Cancel poll timer since we do receive events
                self._poll_timer()
                self._poll_timer = None

            async with self.hass.data[DATA_SONOS].topology_condition:
                group = await _async_extract_group(event)

                if self.unique_id == group[0]:
                    _async_regroup(group)

                    self.hass.data[DATA_SONOS].topology_condition.notify_all()

        if event and not hasattr(event, "zone_player_uui_ds_in_group"):
            return

        self.hass.add_job(_async_handle_group_event(event))

    def update_content(self, event=None):
        """Update information about available content."""
        self._set_favorites()
        self.schedule_update_ha_state()

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        if self._player_volume is None:
            return None
        return self._player_volume / 100

    @property
    def is_volume_muted(self):
        """Return true if volume is muted."""
        return self._player_muted

    @property
    @soco_coordinator
    def shuffle(self):
        """Shuffling state."""
        return self._shuffle

    @property
    @soco_coordinator
    def media_content_id(self):
        """Content id of current playing media."""
        return self._uri

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    @soco_coordinator
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self._media_duration

    @property
    @soco_coordinator
    def media_position(self):
        """Position of current playing media in seconds."""
        return self._media_position

    @property
    @soco_coordinator
    def media_position_updated_at(self):
        """When was the position of the current playing media valid."""
        return self._media_position_updated_at

    @property
    @soco_coordinator
    def media_image_url(self):
        """Image url of current playing media."""
        return self._media_image_url or None

    @property
    @soco_coordinator
    def media_artist(self):
        """Artist of current playing media, music track only."""
        return self._media_artist or None

    @property
    @soco_coordinator
    def media_album_name(self):
        """Album name of current playing media, music track only."""
        return self._media_album_name or None

    @property
    @soco_coordinator
    def media_title(self):
        """Title of current playing media."""
        return self._media_title or None

    @property
    @soco_coordinator
    def queue_position(self):
        """Current position in the playing queue."""
        if self._is_playing_local_queue:
            return self._queue_position

        return None

    @property
    @soco_coordinator
    def source(self):
        """Name of the current input source."""
        return self._source_name or None

    @property
    @soco_coordinator
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_SONOS

    @soco_error()
    def volume_up(self):
        """Volume up media player."""
        self._player.volume += self._volume_increment

    @soco_error()
    def volume_down(self):
        """Volume down media player."""
        self._player.volume -= self._volume_increment

    @soco_error()
    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self.soco.volume = str(int(volume * 100))

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def set_shuffle(self, shuffle):
        """Enable/Disable shuffle mode."""
        self.soco.shuffle = shuffle

    @soco_error()
    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        self.soco.mute = mute

    @soco_error()
    @soco_coordinator
    def select_source(self, source):
        """Select input source."""
        if source == SOURCE_LINEIN:
            self.soco.switch_to_line_in()
        elif source == SOURCE_TV:
            self.soco.switch_to_tv()
        else:
            fav = [fav for fav in self._favorites if fav.title == source]
            if len(fav) == 1:
                src = fav.pop()
                uri = src.reference.get_uri()
                if self.soco.is_radio_uri(uri):
                    self.soco.play_uri(uri, title=source)
                else:
                    self.soco.clear_queue()
                    self.soco.add_to_queue(src.reference)
                    self.soco.play_from_queue(0)

    @property
    @soco_coordinator
    def source_list(self):
        """List of available input sources."""
        sources = [fav.title for fav in self._favorites]

        model = self._model.upper()
        if "PLAY:5" in model or "CONNECT" in model:
            sources += [SOURCE_LINEIN]
        elif "PLAYBAR" in model:
            sources += [SOURCE_LINEIN, SOURCE_TV]
        elif "BEAM" in model or "PLAYBASE" in model:
            sources += [SOURCE_TV]

        return sources

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def media_play(self):
        """Send play command."""
        self.soco.play()

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def media_stop(self):
        """Send stop command."""
        self.soco.stop()

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def media_pause(self):
        """Send pause command."""
        self.soco.pause()

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def media_next_track(self):
        """Send next track command."""
        self.soco.next()

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def media_previous_track(self):
        """Send next track command."""
        self.soco.previous()

    @soco_error(UPNP_ERRORS_TO_IGNORE)
    @soco_coordinator
    def media_seek(self, position):
        """Send seek command."""
        self.soco.seek(str(datetime.timedelta(seconds=int(position))))

    @soco_error()
    @soco_coordinator
    def clear_playlist(self):
        """Clear players playlist."""
        self.soco.clear_queue()

    @soco_error()
    @soco_coordinator
    def play_media(self, media_type, media_id, **kwargs):
        """
        Send the play_media command to the media player.
        If media_type is "playlist", media_id should be a Sonos
        Playlist name.  Otherwise, media_id should be a URI.
        If ATTR_MEDIA_ENQUEUE is True, add `media_id` to the queue.
        """
        if media_type == MEDIA_TYPE_MUSIC:
            if kwargs.get(ATTR_MEDIA_ENQUEUE):
                try:
                    self.soco.add_uri_to_queue(media_id)
                except SoCoUPnPException:
                    _LOGGER.error(
                        'Error parsing media uri "%s", '
                        "please check it's a valid media resource "
                        "supported by Sonos",
                        media_id,
                    )
            else:
                self.soco.play_uri(media_id)
        elif media_type == MEDIA_TYPE_PLAYLIST:
            try:
                playlists = self.soco.get_sonos_playlists()
                playlist = next(p for p in playlists if p.title == media_id)
                self.soco.clear_queue()
                self.soco.add_to_queue(playlist)
                self.soco.play_from_queue(0)
            except StopIteration:
                _LOGGER.error('Could not find a Sonos playlist named "%s"', media_id)
        else:
            _LOGGER.error('Sonos does not support a media type of "%s"', media_type)

    @soco_error()
    def join(self, slaves):
        """Form a group with other players."""
        if self._coordinator:
            self.unjoin()
            group = [self]
        else:
            group = self._sonos_group.copy()

        for slave in slaves:
            if slave.unique_id != self.unique_id:
                slave.soco.join(self.soco)
                # pylint: disable=protected-access
                slave._coordinator = self
                if slave not in group:
                    group.append(slave)

        return group

    @staticmethod
    async def join_multi(hass, master, entities):
        """Form a group with other players."""
        async with hass.data[DATA_SONOS].topology_condition:
            group = await hass.async_add_executor_job(master.join, entities)
            await SonosEntity.wait_for_groups(hass, [group])

    @soco_error()
    def unjoin(self):
        """Unjoin the player from a group."""
        self.soco.unjoin()
        self._coordinator = None

    @staticmethod
    async def unjoin_multi(hass, entities):
        """Unjoin several players from their group."""

        def _unjoin_all(entities):
            """Sync helper."""
            # Unjoin slaves first to prevent inheritance of queues
            coordinators = [e for e in entities if e.is_coordinator]
            slaves = [e for e in entities if not e.is_coordinator]

            for entity in slaves + coordinators:
                entity.unjoin()

        async with hass.data[DATA_SONOS].topology_condition:
            await hass.async_add_executor_job(_unjoin_all, entities)
            await SonosEntity.wait_for_groups(hass, [[e] for e in entities])

    @soco_error()
    def snapshot(self, with_group):
        """Snapshot the state of a player."""
        self._soco_snapshot = pysonos.snapshot.Snapshot(self.soco)
        self._soco_snapshot.snapshot()
        if with_group:
            self._snapshot_group = self._sonos_group.copy()
        else:
            self._snapshot_group = None

    @staticmethod
    async def snapshot_multi(hass, entities, with_group):
        """Snapshot all the entities and optionally their groups."""
        # pylint: disable=protected-access

        def _snapshot_all(entities):
            """Sync helper."""
            for entity in entities:
                entity.snapshot(with_group)

        # Find all affected players
        entities = set(entities)
        if with_group:
            for entity in list(entities):
                entities.update(entity._sonos_group)

        async with hass.data[DATA_SONOS].topology_condition:
            await hass.async_add_executor_job(_snapshot_all, entities)

    @soco_error()
    def restore(self):
        """Restore a snapshotted state to a player."""
        try:
            self._soco_snapshot.restore()
        except (TypeError, AttributeError, SoCoException) as ex:
            # Can happen if restoring a coordinator onto a current slave
            _LOGGER.warning("Error on restore %s: %s", self.entity_id, ex)

        self._soco_snapshot = None
        self._snapshot_group = None

    @staticmethod
    async def restore_multi(hass, entities, with_group):
        """Restore snapshots for all the entities."""
        # pylint: disable=protected-access

        def _restore_groups(entities, with_group):
            """Pause all current coordinators and restore groups."""
            for entity in (e for e in entities if e.is_coordinator):
                if entity.state == STATE_PLAYING:
                    entity.media_pause()

            groups = []

            if with_group:
                # Unjoin slaves first to prevent inheritance of queues
                for entity in [e for e in entities if not e.is_coordinator]:
                    if entity._snapshot_group != entity._sonos_group:
                        entity.unjoin()

                # Bring back the original group topology
                for entity in (e for e in entities if e._snapshot_group):
                    if entity._snapshot_group[0] == entity:
                        entity.join(entity._snapshot_group)
                        groups.append(entity._snapshot_group.copy())

            return groups

        def _restore_players(entities):
            """Restore state of all players."""
            for entity in (e for e in entities if not e.is_coordinator):
                entity.restore()

            for entity in (e for e in entities if e.is_coordinator):
                entity.restore()

        # Find all affected players
        entities = {e for e in entities if e._soco_snapshot}
        if with_group:
            for entity in [e for e in entities if e._snapshot_group]:
                entities.update(entity._snapshot_group)

        async with hass.data[DATA_SONOS].topology_condition:
            groups = await hass.async_add_executor_job(
                _restore_groups, entities, with_group
            )

            await SonosEntity.wait_for_groups(hass, groups)

            await hass.async_add_executor_job(_restore_players, entities)

    @staticmethod
    async def wait_for_groups(hass, groups):
        """Wait until all groups are present, or timeout."""
        # pylint: disable=protected-access

        def _test_groups(groups):
            """Return whether all groups exist now."""
            for group in groups:
                coordinator = group[0]

                # Test that coordinator is coordinating
                current_group = coordinator._sonos_group
                if coordinator != current_group[0]:
                    return False

                # Test that slaves match
                if set(group[1:]) != set(current_group[1:]):
                    return False

            return True

        try:
            with async_timeout.timeout(5):
                while not _test_groups(groups):
                    await hass.data[DATA_SONOS].topology_condition.wait()
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout waiting for target groups %s", groups)

        for entity in hass.data[DATA_SONOS].entities:
            entity.soco._zgs_cache.clear()

    @soco_error()
    @soco_coordinator
    def set_sleep_timer(self, sleep_time):
        """Set the timer on the player."""
        self.soco.set_sleep_timer(sleep_time)

    @soco_error()
    @soco_coordinator
    def clear_sleep_timer(self):
        """Clear the timer on the player."""
        self.soco.set_sleep_timer(None)

    @soco_error()
    @soco_coordinator
    def set_alarm(
        self, alarm_id, time=None, volume=None, enabled=None, include_linked_zones=None
    ):
        """Set the alarm clock on the player."""
        alarm = None
        for one_alarm in alarms.get_alarms(self.soco):
            # pylint: disable=protected-access
            if one_alarm._alarm_id == str(alarm_id):
                alarm = one_alarm
        if alarm is None:
            _LOGGER.warning("did not find alarm with id %s", alarm_id)
            return
        if time is not None:
            alarm.start_time = time
        if volume is not None:
            alarm.volume = int(volume * 100)
        if enabled is not None:
            alarm.enabled = enabled
        if include_linked_zones is not None:
            alarm.include_linked_zones = include_linked_zones
        alarm.save()

    @soco_error()
    def set_option(self, night_sound=None, speech_enhance=None):
        """Modify playback options."""
        if night_sound is not None and self._night_sound is not None:
            self.soco.night_mode = night_sound

        if speech_enhance is not None and self._speech_enhance is not None:
            self.soco.dialog_mode = speech_enhance

    @soco_error()
    def play_queue(self, queue_position=0):
        """Start playing the queue."""
        self.soco.play_from_queue(queue_position)

    @soco_error()
    @soco_coordinator
    def remove_from_queue(self, queue_position=0):
        """Remove item from the queue."""
        self.soco.remove_from_queue(queue_position)

    @property
    def device_state_attributes(self):
        """Return entity specific state attributes."""
        attributes = {ATTR_SONOS_GROUP: [e.entity_id for e in self._sonos_group]}

        if self._night_sound is not None:
            attributes[ATTR_NIGHT_SOUND] = self._night_sound

        if self._speech_enhance is not None:
            attributes[ATTR_SPEECH_ENHANCE] = self._speech_enhance

        if self.queue_position is not None:
            attributes[ATTR_QUEUE_POSITION] = self.queue_position

        return attributes
