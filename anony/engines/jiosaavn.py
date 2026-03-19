# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
#
# Engine A — JioSaavn
# Used for: /play <plain text query>
# Returns: Track with stream_url (320kbps direct audio)
# No cookies. No downloads. No auth required.

import httpx
from anony import config, logger
from anony.helpers import Track
from anony.helpers._utilities import Utilities

utils = Utilities()


class EngineError(Exception):
    pass


class JioSaavn:
    def __init__(self):
        self.base = config.JIOSAAVN_API_URL
        self.client = httpx.AsyncClient(timeout=10)

    async def search(
        self,
        query: str,
        message_id: int,
        video: bool = False,
    ) -> Track:
        """
        Search JioSaavn for a text query.
        Returns Track with stream_url set to 320kbps direct audio URL.
        Raises EngineError if no result or stream unavailable.
        """
        try:
            resp = await self.client.get(
                f"{self.base}/api/search/songs",
                params={"query": query, "limit": 1},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise EngineError(f"JioSaavn search failed: {e}")

        results = data.get("data", {}).get("results", [])
        if not results:
            raise EngineError("jiosaavn_empty")

        song = results[0]
        song_id = song.get("id")

        try:
            detail_resp = await self.client.get(
                f"{self.base}/api/songs/{song_id}"
            )
            detail_resp.raise_for_status()
            detail = detail_resp.json()
        except Exception as e:
            raise EngineError(f"JioSaavn detail fetch failed: {e}")

        song_data = detail.get("data", [{}])
        if isinstance(song_data, list):
            song_data = song_data[0] if song_data else {}

        download_urls = song_data.get("downloadUrl", [])
        stream_url = None
        for item in reversed(download_urls):
            url = item.get("url", "")
            if url and url.startswith("http"):
                stream_url = url
                break

        if not stream_url:
            raise EngineError("jiosaavn_no_stream_url")

        title = song_data.get("name", query)[:50]
        artists = song_data.get("artists", {}).get("primary", [])
        artist = artists[0].get("name", "") if artists else ""
        duration_sec = int(song_data.get("duration", 0))
        duration_str = utils.to_mmss(duration_sec) if duration_sec else "00:00"
        images = song_data.get("image", [])
        thumbnail = images[-1].get("url", "") if images else config.DEFAULT_THUMB
        page_url = song_data.get("url", "https://www.jiosaavn.com")

        logger.info(f"JioSaavn resolved: {title} — {stream_url[:60]}...")

        return Track(
            id=song_id or query,
            channel_name=artist,
            duration=duration_str,
            duration_sec=duration_sec,
            title=title,
            url=page_url,
            stream_url=stream_url,
            message_id=message_id,
            thumbnail=thumbnail,
            view_count=None,
            video=False,
        )

    async def close(self):
        await self.client.aclose()
