"""
Player.

The player function, for all player related things.
"""

from __future__ import annotations

import random
import typing as t
from asyncio import TimeoutError
from asyncio import gather

import hikari

from ongaku import errors
from ongaku.abc.player import PlayerVoice
from ongaku.abc.track import Track
from ongaku.enums import TrackEndReasonType
from ongaku.events import PlayerUpdateEvent
from ongaku.events import QueueEmptyEvent
from ongaku.events import QueueNextEvent
from ongaku.events import TrackEndEvent
from ongaku.internal.logger import TRACE_LEVEL
from ongaku.internal.logger import logger

if t.TYPE_CHECKING:
    from ongaku.abc.player import Player as ABCPlayer
    from ongaku.internal.types import RequestorT
    from ongaku.session import Session

_logger = logger.getChild("player")

__all__ = ("Player",)


class Player:
    """
    Base player.

    The class that allows the player, to play songs, and more.

    Parameters
    ----------
    session
        The session that the player is attached too.
    guild
        The Guild the bot is attached too.
    """

    def __init__(
        self,
        session: Session,
        guild: hikari.SnowflakeishOr[hikari.Guild],
    ):
        self._session = session
        self._guild_id = hikari.Snowflake(guild)
        self._channel_id = None

        self._is_alive = False
        self._is_paused = True

        self._queue: list[Track] = []

        self._voice: PlayerVoice | None = None

        self._session_id: str | None = None

        self._connected: bool = False

        self._volume: int = -1

        self._autoplay = True

        self._position: int = 0

        self.app.subscribe(TrackEndEvent, self._track_end_event)
        self.app.subscribe(PlayerUpdateEvent, self._player_update)

    @property
    def session(self) -> Session:
        """Session.

        The session that is attached to this player.
        """
        return self._session

    @property
    def app(self) -> hikari.GatewayBot:
        """Application.

        The application attached to this player.
        """
        return self.session.client.app

    @property
    def channel_id(self) -> hikari.Snowflake | None:
        """Channel ID.

        The channel id the player is currently in.

        Returns
        -------
        hikari.Snowflake
            The channel ID
        None
            The player is not in a channel.
        """
        return self._channel_id

    @property
    def guild_id(self) -> hikari.Snowflake:
        """Guild ID.

        The guild id attached to this player.
        """
        return self._guild_id

    @property
    def is_alive(self) -> bool:
        """Is alive.

        Whether the bot is alive or not. True if alive.
        """
        return self._is_alive

    @property
    def position(self) -> int:
        """Position.

        The position of the track in milliseconds.
        """
        return self._position

    @property
    def volume(self) -> int:
        """
        The volume of the player.

        !!! note
            If volume is -1, it has either not been updated, or connected to lavalink.
        """
        return self._volume

    @property
    def is_paused(self) -> bool:
        """Is paused.

        Whether the player is paused or not. True if paused.
        """
        return self._is_paused

    @property
    def autoplay(self) -> bool:
        """Autoplay.

        Whether or not the next song will play, when this song ends.
        """
        return self._autoplay

    @property
    def connected(self) -> bool:
        """Connected.

        Whether or not the bot is connected to a voice channel.
        """
        return self._connected

    @property
    def queue(self) -> t.Sequence[Track]:
        """Queue.

        Returns the current queue of tracks.
        """
        return self._queue

    async def connect(
        self,
        channel: hikari.SnowflakeishOr[hikari.GuildVoiceChannel],
        *,
        mute: bool = False,
        deaf: bool = True,
    ) -> None:
        """Connect.

        Parameters
        ----------
        channel
            The channel (or channel id) that you wish to connect the bot to.
        mute
            Whether or not to mute the app.
        deaf
            Whether or not to deafen the app.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        PlayerConnectException
            Raised when the voice state of the bot cannot be updated, or the voice events required could not be received.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        _logger.log(
            TRACE_LEVEL,
            f"Attempting connection to voice channel: {hikari.Snowflake(channel)} in guild: {self.guild_id}",
        )

        self._channel_id = hikari.Snowflake(channel)

        try:
            await self.app.update_voice_state(
                self.guild_id, self._channel_id, self_mute=mute, self_deaf=deaf
            )
        except Exception as e:
            raise errors.PlayerConnectException(str(e))

        _logger.log(
            TRACE_LEVEL,
            f"waiting for voice events for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        try:
            state_event, server_event = await gather(
                self.app.wait_for(
                    hikari.VoiceStateUpdateEvent,
                    timeout=5,
                ),
                self.app.wait_for(
                    hikari.VoiceServerUpdateEvent,
                    timeout=5,
                ),
            )
        except TimeoutError as e:
            raise errors.PlayerConnectException(
                f"Could not connect to voice channel {self.channel_id} in {self.guild_id} due to events not being received.",
            )

        if server_event.endpoint is None:
            raise errors.PlayerConnectException(
                f"Endpoint missing for attempted server connection for voice channel {self.channel_id} in {self.guild_id}",
            )

        _logger.log(
            TRACE_LEVEL,
            f"Successfully received events for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        self._voice = PlayerVoice(
            token=server_event.token,
            endpoint=server_event.endpoint,
            session_id=state_event.state.session_id,
        )

        try:
            player = await self.session.client.rest.update_player(
                session,
                self.guild_id,
                voice=self._voice,
                no_replace=False,
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        self._connected = True

        _logger.log(
            TRACE_LEVEL,
            f"Successfully connected, and sent data to lavalink for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        await self._update(player)

    async def disconnect(self) -> None:
        """
        Disconnect player.

        Disconnect the player from the lavalink server, and discord.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        self._is_alive = False
        await self.clear()

        _logger.log(
            TRACE_LEVEL,
            f"Attempting to delete player for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        try:
            await self.session.client.rest.delete_player(session, self._guild_id)
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        _logger.log(
            TRACE_LEVEL,
            f"Successfully deleted player for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        self._connected = False

        _logger.log(
            TRACE_LEVEL,
            f"Updating voice state for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        await self.app.update_voice_state(self.guild_id, None)

        _logger.log(
            TRACE_LEVEL,
            f"Successfully updated voice state for channel: {self.channel_id} in guild: {self.guild_id}",
        )

    async def play(
        self, track: Track | None = None, requestor: RequestorT | None = None
    ) -> None:
        """Play.

        Play a new track, or start the playing of the queue.

        Parameters
        ----------
        track
            The track you wish to play. If none, pulls from the queue.
        requestor
            The member who requested the track.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        PlayerConnectException
            Raised when the player is not connected to a channel.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        if self.channel_id is None:
            raise errors.PlayerConnectException("Not connected to a channel.")

        if len(self.queue) <= 0 and track == None:
            raise errors.PlayerQueueException("Queue is empty.")

        if track:
            if requestor:
                track.requestor = hikari.Snowflake(requestor)

            self._queue.insert(0, track)

        try:
            player = await self.session.client.rest.update_player(
                session,
                self.guild_id,
                track=self.queue[0],
                no_replace=False,
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        self._is_paused = False

        await self._update(player)

    async def add(
        self, tracks: t.Sequence[Track] | Track, requestor: RequestorT | None = None
    ) -> None:
        """
        Add tracks.

        Add tracks to the queue.

        !!! note
            This will not automatically start playing the songs. please call `.play()` after, with no track, if the player is not already playing.

        Parameters
        ----------
        tracks
            The list of tracks or a singular track you wish to add to the queue.
        requestor
            The user/member who requested the song.
        """
        new_requestor = None

        if requestor:
            new_requestor = hikari.Snowflake(requestor)

        if isinstance(tracks, Track):
            if requestor:
                tracks.requestor = new_requestor
            self._queue.append(tracks)
            return

        for track in tracks:
            if requestor:
                track.requestor = new_requestor
            self._queue.append(track)

    async def pause(self, value: bool | None = None) -> None:
        """
        Pause the player.

        Allows for the user to pause the currently playing track on this player.

        !!! info
            `True` will force pause the bot, `False` will force unpause the bot. Leaving it empty, will toggle it from its current state.

        Parameters
        ----------
        value
            How you wish to pause the bot.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        if value:
            self._is_paused = value
        else:
            self._is_paused = not self.is_paused

        try:
            player = await self.session.client.rest.update_player(
                session, self.guild_id, paused=self.is_paused
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        await self._update(player)

    async def stop(self) -> None:
        """
        Stop current track.

        Stops the audio, by setting the song to none.

        !!! note
            This does not touch the current queue, just clears the player of its track.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        try:
            player = await self.session.client.rest.update_player(
                session,
                self.guild_id,
                track=None,
                no_replace=False,
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        self._is_paused = True

        await self._update(player)

    async def shuffle(self) -> None:
        """Shuffle.

        Shuffle the current queue.

        !!! note
            This will not touch the first track.

        Raises
        ------
        PlayerQueueException
            Raised when the queue has 2 or less tracks in it.
        """
        if len(self.queue) <= 2:
            raise PlayerQueueException(
                self.guild_id, "Queue must have more than 2 tracks to shuffle."
            )

        new_queue = list(self.queue)

        first_track = new_queue.pop(0)

        random.shuffle(new_queue)

        new_queue.insert(0, first_track)

        self._queue = new_queue

    async def skip(self, amount: int = 1) -> None:
        """
        Skip songs.

        skip a selected amount of songs in the queue.

        Parameters
        ----------
        amount
            The amount of songs you wish to skip.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        ValueError
            Raised when the amount set is 0 or negative.
        PlayerQueueException
            Raised when the queue is empty.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        if amount <= 0:
            raise ValueError(f"Skip amount cannot be 0 or negative. Value: {amount}")
        if len(self.queue) == 0:
            raise errors.PlayerQueueException("Queue is empty.")

        for _ in range(amount):
            if len(self._queue) == 0:
                break
            else:
                self._queue.pop(0)

        if len(self.queue) <= 0:
            try:
                player = await self.session.client.rest.update_player(
                    session,
                    self.guild_id,
                    track=None,
                    no_replace=False,
                )
            except errors.RestEmptyException:
                raise
            except errors.RestStatusException:
                raise
            except errors.RestErrorException:
                raise
            except errors.BuildException:
                raise

            await self._update(player)
        else:
            try:
                player = await self.session.client.rest.update_player(
                    session,
                    self.guild_id,
                    track=self.queue[0],
                    no_replace=False,
                )
            except errors.RestEmptyException:
                raise
            except errors.RestStatusException:
                raise
            except errors.RestErrorException:
                raise
            except errors.BuildException:
                raise

            await self._update(player)

    async def remove(self, value: Track | int) -> None:
        """
        Remove track.

        Removes the track, or the track in that position.

        !!! warning
            This does not stop the track if its in the first position.

        Parameters
        ----------
        value
            Remove a selected track. If [Track][ongaku.abc.track.Track], then it will remove the first occurrence of that track. If an integer, it will remove the track at that position.

        Raises
        ------
        PlayerQueueException
            Raised when the removal of a track fails.
        """
        if len(self.queue) == 0:
            raise errors.PlayerQueueException("Queue is empty.")

        if isinstance(value, Track):
            index = self._queue.index(value)

        else:
            index = value

        try:
            self._queue.pop(index)
        except KeyError:
            if isinstance(value, Track):
                raise errors.PlayerQueueException(
                    f"Failed to remove song: {value.info.title}"
                )
            else:
                raise errors.PlayerQueueException(
                    f"Failed to remove song in position {value}"
                )

    async def clear(self) -> None:
        """
        Clear the queue.

        Clear the current queue, and also stop the audio from the player.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        self._queue.clear()

        session = self.session._get_session_id()

        try:
            player = await self.session.client.rest.update_player(
                session,
                self.guild_id,
                track=None,
                no_replace=False,
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        await self._update(player)

    async def set_autoplay(self, enable: bool | None = None) -> bool:
        """
        Set autoplay.

        whether or not to enable or disable autoplay.

        Parameters
        ----------
        enable
            Whether or not to enable autoplay. If left empty, it will toggle the current status.
        """
        if enable:
            self._autoplay = enable
            return self._autoplay

        self._autoplay = not self._autoplay
        return self._autoplay

    async def set_volume(self, volume: int) -> None:
        """
        Set the volume.

        The volume you wish to set for the player.

        Parameters
        ----------
        volume
            The volume you wish to set, from 0 to 1000.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        ValueError
            Raised when the value is below 0, or above 1000.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        if volume < 0:
            raise ValueError(f"Volume cannot be below zero. Volume: {volume}")
        if volume > 1000:
            raise ValueError(f"Volume cannot be above 1000. Volume: {volume}")

        try:
            player = await self.session.client.rest.update_player(
                session,
                self.guild_id,
                volume=volume,
                no_replace=False,
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        await self._update(player)

    async def set_position(self, value: int) -> None:
        """
        Change the track position.

        Change the currently playing track's position.

        Parameters
        ----------
        value
            The value, of the position, in milliseconds.

        Raises
        ------
        SessionStartException
            Raised when the players session has not yet been started.
        ValueError
            Raised when the position is negative.
        PlayerQueueException
            Raised when the queue is empty.
        RestEmptyException
            Raised when a return type was requested, yet nothing was received.
        RestStatusException
            Raised when nothing was received, but a 4XX/5XX error was reported.
        RestErrorException
            Raised when a rest error is returned with a 4XX/5XX error.
        BuildException
            Raised when a construction of a ABC class fails.
        """
        session = self.session._get_session_id()

        if value < 0:
            raise ValueError("Sorry, but a negative value is not allowed.")

        if len(self.queue) <= 0:
            raise errors.PlayerQueueException("Queue is empty.")

        try:
            player = await self.session.client.rest.update_player(
                session,
                self.guild_id,
                position=value,
                no_replace=False,
            )
        except errors.RestEmptyException:
            raise
        except errors.RestStatusException:
            raise
        except errors.RestErrorException:
            raise
        except errors.BuildException:
            raise

        await self._update(player)

    async def transfer_player(self, session: Session) -> Player:
        """Transfer player.

        Transfer this player to another player.

        !!! warning
            This will kill the current player the function is ran on.

        Parameters
        ----------
        session
            The session you wish to add the new player to.

        Returns
        -------
        Player
            The new player.
        """
        new_player = Player(session, self.guild_id)

        await new_player.add(self.queue)

        if self.connected and self.channel_id:
            await self.disconnect()

            await new_player.connect(self.channel_id)

            if not self.is_paused:
                await new_player.play()
                await new_player.set_position(self.position)

        return new_player

    async def _update(self, player: ABCPlayer) -> None:
        _logger.log(
            TRACE_LEVEL,
            f"Updating player for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        self._is_paused = player.is_paused
        self._voice = player.voice
        self._volume = player.volume

    async def _track_end_event(self, event: TrackEndEvent) -> None:
        self.session._get_session_id()

        if not self.autoplay:
            return

        if event.reason != TrackEndReasonType.FINISHED:
            return

        _logger.log(
            TRACE_LEVEL,
            f"Auto-playing track for channel: {self.channel_id} in guild: {self.guild_id}",
        )

        if int(event.guild_id) == int(self.guild_id):
            _logger.log(
                TRACE_LEVEL,
                f"Removing current track from queue for channel: {self.channel_id} in guild: {self.guild_id}",
            )
            try:
                await self.remove(0)
            except ValueError:
                await self.app.dispatch(
                    QueueEmptyEvent(
                        self.app,
                        event.client,
                        event.session,
                        self.guild_id,
                    )
                )
                return

            if len(self.queue) <= 0:
                _logger.log(
                    TRACE_LEVEL,
                    f"Auto-play has empty queue for channel: {self.channel_id} in guild: {self.guild_id}",
                )
                await self.app.dispatch(
                    QueueEmptyEvent(
                        self.app,
                        event.client,
                        event.session,
                        self.guild_id,
                    )
                )
                return

            _logger.log(
                TRACE_LEVEL,
                f"Auto-playing next track for channel: {self.channel_id} in guild: {self.guild_id}. Track title: {self.queue[0].info.title}",
            )

            await self.play()

            await self.app.dispatch(
                QueueNextEvent(
                    self.app,
                    event.client,
                    event.session,
                    self.guild_id,
                    self._queue[0],
                    event.track,
                )
            )

            _logger.log(
                TRACE_LEVEL,
                f"Auto-playing successfully completed for channel: {self.channel_id} in guild: {self.guild_id}",
            )

    async def _player_update(self, event: PlayerUpdateEvent) -> None:
        if event.guild_id != self.guild_id:
            return

        if not event.state.connected:
            await self.stop()

        self._position = event.state.position


# MIT License

# Copyright (c) 2023 MPlatypus

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
