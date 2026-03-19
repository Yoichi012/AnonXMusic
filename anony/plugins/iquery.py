# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import httpx
from pyrogram import types
from anony import app, config
from anony.helpers import buttons


@app.on_inline_query(~app.bl_users)
async def inline_query_handler(_, query: types.InlineQuery):
    text = query.query.strip().lower()
    if not text:
        return
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"{config.JIOSAAVN_API_URL}/api/search/songs",
                params={"query": text, "limit": 15},
            )
            resp.raise_for_status()
            data = resp.json()

        results_data = data.get("data", {}).get("results", [])
        answers = []

        for song in results_data:
            title = song.get("name", "Unknown Title")
            artists = song.get("artists", {}).get("primary", [])
            artist_name = artists[0].get("name", "Unknown") if artists else "Unknown"
            duration_sec = int(song.get("duration", 0))
            minutes, seconds = divmod(duration_sec, 60)
            duration_str = f"{minutes}:{seconds:02d}"
            images = song.get("image", [])
            thumbnail = images[-1].get("url", "") if images else config.DEFAULT_THUMB
            page_url = song.get("url", "https://www.jiosaavn.com")

            caption = (
                f"<b>Title:</b> <a href='{page_url}'>{title[:250]}</a>\n\n"
                f"<b>Duration:</b> {duration_str}\n"
                f"<b>Artist:</b> {artist_name}\n\n"
                f"<u><i>Fetched by {app.name}</i></u>"
            )
            answers.append(
                types.InlineQueryResultPhoto(
                    photo_url=thumbnail,
                    title=title,
                    description=f"{artist_name} | {duration_str}",
                    caption=caption,
                    reply_markup=buttons.yt_key(page_url),
                )
            )

        if answers:
            await app.answer_inline_query(query.id, results=answers, cache_time=5)
    except Exception:
        pass
