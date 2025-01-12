"""
Info ABC's.

The info abstract classes.
"""

from __future__ import annotations

import typing

import msgspec

from ongaku.abc.bases import PayloadBase

__all__ = (
    "InfoVersion",
    "InfoGit",
    "InfoPlugin",
    "Info",
)


class InfoVersion(PayloadBase):
    """
    Version information.

    All information, about the version of lavalink that is running.

    ![Lavalink](../../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest.html#version-object)
    """

    semver: str
    """The full version string of this Lavalink server."""
    major: int
    """The major version of this Lavalink server."""
    minor: int
    """The minor version of this Lavalink server."""
    patch: int
    """The patch version of this Lavalink server."""
    pre_release: str = msgspec.field(name="preRelease")
    """The pre-release version according to semver as a `.` separated list of identifiers."""
    build: str | None = msgspec.field(default=None)
    """The build metadata according to semver as a `.` separated list of identifiers."""


class InfoGit(PayloadBase):
    """
    Git information.

    All of the information about the lavalink git information.

    ![Lavalink](../../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest.html#git-object)
    """

    branch: str
    """The branch this Lavalink server was built on."""
    commit: str
    """The commit this Lavalink server was built on."""
    commit_time: int = msgspec.field(name="commitTime")
    """The millisecond unix timestamp for when the commit was created."""


class InfoPlugin(PayloadBase):
    """
    Plugin information.

    All of the Information about the currently loaded plugins.

    ![Lavalink](../../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest.html#plugin-object)
    """

    name: str
    """The name of the plugin."""
    version: str
    """The version of the plugin."""


class Info(PayloadBase):
    """
    Information.

    All of the Info Version information.

    ![Lavalink](../../assets/lavalink_logo.png){ height="18" width="18"} [Reference](https://lavalink.dev/api/rest.html#info-response)
    """

    version: InfoVersion
    """The version of this Lavalink server."""
    build_time: int = msgspec.field(name="buildTime")
    """The millisecond unix timestamp when this Lavalink jar was built."""
    git: InfoGit
    """The git information of this Lavalink server."""
    jvm: str
    """The JVM version this Lavalink server runs on."""
    lavaplayer: str
    """The Lavaplayer version being used by this server."""
    source_managers: typing.Sequence[str] = msgspec.field(name="sourceManagers")
    """The enabled source managers for this server."""
    filters: typing.Sequence[str]
    """The enabled filters for this server."""
    plugins: typing.Sequence[InfoPlugin]
    """The enabled plugins for this server."""


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
