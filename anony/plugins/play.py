# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pyrogram import filters, types

from anony import anon, app, config, db, lang, queue, tg
from anony.engines.router import SmartRouter
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB

router = SmartRouter()


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    sent = await m.reply_text(m.lang["play_searching"])
    mention = m.from_user.mention

    # Case 1: Telegram file reply
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)
        if not file:
            return
        file.user = mention
        if force:
            queue.force_add(m.chat.id, file)
        else:
            position = queue.add(m.chat.id, file)
            if position != 0 or await db.get_call(m.chat.id):
                return await sent.edit_text(
                    m.lang["play_queued"].format(
                        position, file.url or "", file.title, file.duration, mention
                    )
                )
        await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
        return

    # Case 2: M3U8 direct stream
    if m3u8 and url:
        file = await tg.process_m3u8(url, sent.id, video)
        file.user = mention
        if force:
            queue.force_add(m.chat.id, file)
        else:
            position = queue.add(m.chat.id, file)
            if position != 0 or await db.get_call(m.chat.id):
                return await sent.edit_text(
                    m.lang["play_queued"].format(
                        position, file.url or "", file.title, file.duration, mention
                    )
                )
        await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
        return

    # Case 3: Smart Router (text or URL)
    query = url if url else (
        " ".join(m.command[1:]) if len(m.command) >= 2 else None
    )
    if not query:
        return await sent.edit_text(m.lang["play_usage"])

    track = await router.resolve(
        query=query,
        video=video,
        message_id=sent.id,
        requested_by=mention,
        chat_id=m.chat.id,
    )

    if not track:
        return await sent.edit_text(
            m.lang["play_not_found"].format(config.SUPPORT_CHAT)
        )

    if track.duration_sec and track.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, track.title, track.duration)

    track.user = mention

    if force:
        queue.force_add(m.chat.id, track)
    else:
        position = queue.add(m.chat.id, track)
        if position != 0 or await db.get_call(m.chat.id):
            await sent.edit_text(
                m.lang["play_queued"].format(
                    position, track.url or "", track.title, track.duration, mention,
                ),
                reply_markup=buttons.play_queued(
                    m.chat.id, track.id, m.lang["play_now"]
                ),
            )
            return

    await anon.play_media(chat_id=m.chat.id, message=sent, media=track)
