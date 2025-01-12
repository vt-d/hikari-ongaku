"""
Enums.

All of the enums for the entire library.
"""

from __future__ import annotations

import enum

__all__ = (
    "SeverityType",
    "TrackEndReasonType",
    "BandType",
    "RoutePlannerType",
    "IPBlockType",
    "SessionStatus",
)


class SessionStatus(int, enum.Enum):
    """
    Session Status.

    The status of the session.
    """

    NOT_CONNECTED = 0
    """Is not currently connected to its server."""
    CONNECTED = 1
    """Has successfully connected to its server."""
    FAILURE = 2
    """Failure to connect to its server."""


class SeverityType(str, enum.Enum):
    """
    Track error severity type.

    The severity type of the lavalink track error.

    ![Lavalink](../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/websocket#severity)
    """

    COMMON = "common"
    """The cause is known and expected, indicates that there is nothing wrong with the library itself"""
    SUSPICIOUS = "suspicious"
    """The cause might not be exactly known, but is possibly caused by outside factors. For example when an outside service responds in a format that we do not expect"""
    FAULT = "fault"
    """The probable cause is an issue with the library or there is no way to tell what the cause might be. This is the default level and other levels are used in cases where the thrower has more in-depth knowledge about the error"""


class TrackEndReasonType(str, enum.Enum):
    """
    Track end reason type.

    The track end reason type for the track that was just playing.

    ![Lavalink](../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/websocket#track-end-reason)
    """

    FINISHED = "finished"
    """The track finished playing."""
    LOADFAILED = "loadFailed"
    """The track failed to load."""
    STOPPED = "stopped"
    """The track was stopped."""
    REPLACED = "replaced"
    """The track was replaced."""
    CLEANUP = "cleanup"
    """The track was cleaned up."""


class BandType(enum.IntEnum):
    """
    Band type.

    The band values, available for use in lavalink

    ![Lavalink](../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest#equalizer)
    """

    HZ25 = 0
    """25 Hz"""
    HZ40 = 1
    """40 Hz"""
    HZ63 = 2
    """63 Hz"""
    HZ100 = 3
    """100 Hz"""
    HZ160 = 4
    """160 Hz"""
    HZ250 = 5
    """250 Hz"""
    HZ400 = 6
    """400 Hz"""
    HZ630 = 7
    """630 Hz"""
    HZ1000 = 8
    """1000 Hz"""
    HZ1600 = 9
    """1600 Hz"""
    HZ2500 = 10
    """2500 Hz"""
    HZ4000 = 11
    """4000 Hz"""
    HZ6300 = 12
    """6300 Hz"""
    HZ10000 = 13
    """10000 Hz"""
    HZ16000 = 14
    """16000 Hz"""


class RoutePlannerType(str, enum.Enum):
    """
    Route Planner Type.

    The type of routeplanner that the server is currently using.

    ![Lavalink](../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest#route-planner-types)
    """

    ROTATING_ROUTE_PLANNER = "RotatingIpRoutePlanner"
    """IP address used is switched on ban. Recommended for IPv4 blocks or IPv6 blocks smaller than a /64."""
    NANO_IP_ROUTE_PLANNER = "NanoIpRoutePlanner"
    """IP address used is switched on clock update. Use with at least 1 /64 IPv6 block."""
    ROTATING_NANO_IP_ROUTE_PLANNER = "RotatingNanoIpRoutePlanner"
    """IP address used is switched on clock update, rotates to a different /64 block on ban. Use with at least 2x /64 IPv6 blocks."""
    BALANCING_IP_ROUTE_PLANNER = "BalancingIpRoutePlanner"
    """IP address used is selected at random per request. Recommended for larger IP blocks."""


class IPBlockType(str, enum.Enum):
    """
    IP Block Type.

    The IP Block type, 4, or 6.

    ![Lavalink](../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest#ip-block-type)
    """

    INET_4_ADDRESS = "Inet4Address"
    """The ipv4 block type"""
    INET_6_ADDRESS = "Inet6Address"
    """The ipv6 block type"""


class WebsocketOPCode(str, enum.Enum):
    READY = "ready"
    PLAYER_UPDATE = "playerUpdate"
    STATS = "stats"
    EVENT = "event"


class WebsocketEvent(str, enum.Enum):
    TRACK_START_EVENT = "TrackStartEvent"
    TRACK_END_EVENT = "TrackEndEvent"
    TRACK_EXCEPTION_EVENT = "TrackExceptionEvent"
    TRACK_STUCK_EVENT = "TrackStuckEvent"
    WEBSOCKET_CLOSED_EVENT = "WebSocketClosedEvent"


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
