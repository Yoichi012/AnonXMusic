# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
#
# Smart Router — decides which engine handles the request.
#
# /vplay <anything>       → Cobalt (video=True)
# /play <yt/spotify URL>  → Cobalt (audio only)
# /play <plain text>      → JioSaavn → fallback None

import re
from anony import logger
from anony.engines.jiosaavn import JioSaavn, EngineError as JSError
from anony.engines.cobalt import Cobalt, EngineError as CobaltError
from anony.helpers import Track


URL_REGEX = re.compile(r"https?://[^\s]+")

YT_SPOTIFY_REGEX = re.compile(
    r"https?://(?:www\.|m\.)?(?:"
    r"youtube\.com/(?:watch\?v=|shorts/|playlist\?list=)"
    r"|youtu\.be/"
    r"|spotify\.com/(?:track|album|playlist)/"
    r"|soundcloud\.com/"
    r")[^\s]+"
)


class SmartRouter:
    def __init__(self):
        self.jiosaavn = JioSaavn()
        self.cobalt = Cobalt()

    def _is_url(self, text: str) -> bool:
        return bool(URL_REGEX.match(text.strip()))

    async def resolve(
        self,
        query: str,
        video: bool,
        message_id: int,
        requested_by: str,
        chat_id: int,
    ) -> Track | None:
        query = query.strip()

        # vplay or URL → Cobalt
        if video or self._is_url(query):
            try:
                track = await self.cobalt.resolve(
                    url=query,
                    message_id=message_id,
                    video=video,
                )
                track.user = requested_by
                return track
            except CobaltError as e:
                logger.error(f"Cobalt failed: {e}")
                return None

        # Plain text → JioSaavn
        try:
            track = await self.jiosaavn.search(
                query=query,
                message_id=message_id,
            )
            track.user = requested_by
            return track
        except JSError as e:
            logger.error(f"JioSaavn failed: {e}")
            return None

    async def close(self):
        await self.jiosaavn.close()
        await self.cobalt.close()
