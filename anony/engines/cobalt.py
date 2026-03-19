# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
#
# Engine B — Local Cobalt API
# Used for: /play <youtube/spotify URL>, /vplay <anything>
# Cobalt runs on Docker: http://127.0.0.1:9000
# No cookies. No yt-dlp. No downloads.

import re
import httpx
from anony import config, logger
from anony.helpers import Track
from anony.helpers._utilities import Utilities

utils = Utilities()


class EngineError(Exception):
    pass


YT_ID_REGEX = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)


class Cobalt:
    def __init__(self):
        self.api_url = f"{config.COBALT_URL}/api/json"
        self.client = httpx.AsyncClient(timeout=20)

    async def get_stream_url(self, url: str, is_audio_only: bool = True) -> str:
        payload = {
            "url": url,
            "isAudioOnly": is_audio_only,
            "aFormat": "mp3",
            "audioQuality": "320",
        }
        try:
            resp = await self.client.post(
                self.api_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.ConnectError:
            raise EngineError(
                "Cobalt API is not running. "
                "Start it: docker compose -f docker/cobalt-compose.yml up -d"
            )
        except Exception as e:
            raise EngineError(f"Cobalt request failed: {e}")

        status = data.get("status", "")
        if status == "stream":
            return data["url"]
        elif status == "redirect":
            return data["url"]
        elif status == "picker":
            items = data.get("picker", [])
            if items:
                return items[0]["url"]
            raise EngineError("cobalt_picker_empty")
        elif status == "error":
            raise EngineError(f"cobalt_error: {data.get('text', 'unknown')}")
        else:
            raise EngineError(f"cobalt_unknown_status: {status}")

    def _extract_yt_id(self, url: str) -> str | None:
        match = YT_ID_REGEX.search(url)
        return match.group(1) if match else None

    async def resolve(
        self,
        url: str,
        message_id: int,
        video: bool = False,
        title: str = None,
    ) -> Track:
        is_audio_only = not video
        stream_url = await self.get_stream_url(url, is_audio_only)

        yt_id = self._extract_yt_id(url)
        thumbnail = (
            f"https://i.ytimg.com/vi/{yt_id}/maxresdefault.jpg"
            if yt_id else config.DEFAULT_THUMB
        )
        display_title = title or (
            f"YouTube: {yt_id}" if yt_id else url.split("/")[-1][:50]
        )

        logger.info(f"Cobalt resolved: {display_title} — {stream_url[:60]}...")

        return Track(
            id=yt_id or url,
            channel_name=None,
            duration="00:00",
            duration_sec=0,
            title=display_title[:50],
            url=url,
            stream_url=stream_url,
            message_id=message_id,
            thumbnail=thumbnail,
            view_count=None,
            video=video,
        )

    async def close(self):
        await self.client.aclose()
