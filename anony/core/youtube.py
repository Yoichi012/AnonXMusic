# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os
import re
import yt_dlp
import asyncio
import aiohttp
from pathlib import Path
from glob import glob

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils


class _YTLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg):
        skip_keywords = [
            "jsc", "0.7.0", "challenge", "PO Token",
            "po_token", "GVS", "n challenge", "skipping",
            "No title found"
        ]
        if not any(k.lower() in msg.lower() for k in skip_keywords):
            logger.warning(msg)
    def error(self, msg):
        logger.error(msg)


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
        except Exception:
            return None
        if results and results["result"]:
            data = results["result"][0]
            return Track(
                id=data.get("id"),
                channel_name=data.get("channel", {}).get("name"),
                duration=data.get("duration"),
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=data.get("title")[:25],
                thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                url=data.get("link"),
                view_count=data.get("viewCount", {}).get("short"),
                video=video,
            )
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    def _find_downloaded_file(self, video_id: str) -> str | None:
        matches = glob(f"downloads/{video_id}.*")
        matches = [f for f in matches if not f.endswith(".part")]
        return matches[0] if matches else None

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id

        existing = self._find_downloaded_file(video_id)
        if existing:
            return existing

        base_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "logger": _YTLogger(),
            "noplaylist": True,
            "geo_bypass": True,
            "overwrites": False,
            "nocheckcertificate": True,
            "check_formats": False,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                }
            },
        }

        if video:
            ydl_opts = {
                **base_opts,
                "format": (
                    "bestvideo[height<=?720][ext=mp4]+bestaudio[ext=m4a]/"
                    "bestvideo[height<=?720]+bestaudio/18"
                ),
                "merge_output_format": "mp4",
            }
        else:
            ydl_opts = {
                **base_opts,
                "format": "251/250/249/140/bestaudio/best",
            }

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
                    logger.error("yt-dlp error: %s", e)
                    return None
                except Exception as ex:
                    logger.warning("Download failed: %s", ex)
                    return None
            return self._find_downloaded_file(video_id)

        return await asyncio.to_thread(_download)
