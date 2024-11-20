#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import os
import re

import yt_dlp
from pykeyboard import InlineKeyboard

from telethon import Button, events
from telethon.tl.types import DocumentAttributeFilename


from config import BANNED_USERS, SONG_DOWNLOAD_DURATION, SONG_DOWNLOAD_DURATION_LIMIT
from strings import get_command
from YukkiMusic import YouTube, app
from YukkiMusic.platforms.Youtube import get_ytdl_options
from YukkiMusic.utils.decorators.language import language, languageCB
from YukkiMusic.utils.formatters import convert_bytes
from YukkiMusic.utils.inline.song import song_markup

# Command

SONG_COMMAND = get_command("SONG_COMMAND")


@app.on_message(
    command=SONG_COMMAND,
    is_group=True,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@language
async def song_commad_group(e, _):
    upl = [
        [
            Button.url(
                text=_["SG_B_1"],
                url=f"https://t.me/{app.username}?start=song",
            ),
        ]
    ]
    await e.reply(_["song_1"], buttons=upl)


# Song Module


@app.on_message(
    command=SONG_COMMAND,
    is_private=True,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@language
async def song_commad_private(event, _):

    await event.delete()
    url = await YouTube.url(event)
    if url:
        if not await YouTube.exists(url):
            return await event.reply(_["song_5"])
        mystic = await event.reply(_["play_1"])
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(url)
        if str(duration_min) == "None":
            return await mystic.edit(_["song_3"])

        if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
            return await mystic.edit(
                _["play_4"].format(SONG_DOWNLOAD_DURATION, duration_min)
            )
        buttons = song_markup(_, vidid)
        await mystic.delete()
        return await event.reply(
            file=thumbnail,
            message=_["song_4"].format(title),
            buttons=buttons,
        )

    else:
        if len(event.text.split()) < 2:
            return await event.reply(_["song_2"])
    mystic = await event.reply(_["play_1"])
    query = event.text.split(None, 1)[1]

    try:
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(query)
    except:
        return await mystic.edit(_["play_3"])
    if str(duration_min) == "None":
        return await mystic.edit(_["song_3"])
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit(
            _["play_6"].format(SONG_DOWNLOAD_DURATION, duration_min)
        )
    buttons = song_markup(_, vidid)
    await mystic.delete()
    return await event.reply(
        file=thumbnail,
        message=_["song_4"].format(title),
        buttons=buttons,
    )


@app.on(
    events.CallbackQuery(
        pattern=r"song_back", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def songs_back_helper(event, _):

    cb_data = event.data.decode("utf-8").strip()
    request = cb_data.split(None, 1)[1]
    stype, vidid = request.split("|")
    buttons = song_markup(_, vidid)
    return await event.edit(buttons=buttons)


@app.on(
    events.CallbackQuery(
        pattern=r"song_helper", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def song_helper_cb(event, _):
    cb_data = event.data.decode("utf-8").strip()
    cb_request = cb_data.split(None, 1)[1]
    stype, vidid = cb_request.split("|")
    try:
        await event.answer(_["song_6"], alert=True)
    except:
        pass
    if stype == "audio":
        try:
            formats_available, link = await YouTube.formats(vidid, True)
        except:
            return await event.edit(_["song_7"])
        keyboard = InlineKeyboard()
        done = []
        for x in formats_available:
            check = x["format"]
            if "audio" in check:
                if x["filesize"] is None:
                    continue
                form = x["format_note"].title()
                if form not in done:
                    done.append(form)
                else:
                    continue
                sz = convert_bytes(x["filesize"])
                fom = x["format_id"]
                keyboard.row(
                    Button.inline(
                        text=f"{form} Quality Audio = {sz}",
                        data=f"song_download {stype}|{fom}|{vidid}",
                    ),
                )

        keyboard.row(
            Button.inline(
                text=_["BACK_BUTTON"],
                data=f"song_back {stype}|{vidid}",
            ),
            Button.inline(text=_["CLOSE_BUTTON"], data=f"close"),
        )
        return await event.edit(buttons=keyboard)
    else:
        try:
            formats_available, link = await YouTube.formats(vidid, True)
        except Exception:
            return await event.edit(_["song_7"])
        keyboard = InlineKeyboard()
        done = [160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266]
        for x in formats_available:
            check = x["format"]
            if x["filesize"] is None:
                continue
            if int(x["format_id"]) not in done:
                continue
            sz = convert_bytes(x["filesize"])
            ap = check.split("-")[1]
            to = f"{ap} = {sz}"
            keyboard.row(
                Button.inline(
                    text=to,
                    data=f"song_download {stype}|{x['format_id']}|{vidid}",
                )
            )
        keyboard.row(
            Button.inline(
                text=_["BACK_BUTTON"],
                data=f"song_back {stype}|{vidid}",
            ),
            Button.inline(text=_["CLOSE_BUTTON"], data=f"close"),
        )
        return await event.edit(buttons=keyboard)


# Downloading Songs Here


@app.on(
    events.CallbackQuery(
        pattern=r"song_download", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def song_download_cb(event, _):
    try:
        await event.answer("Downloading...")
    except:
        pass
    cb_data = event.data.decode("utf-8").strip()
    cb_request = cb_data.split(None, 1)[1]
    stype, format_id, vidid = cb_request.split("|")
    mystic = await event.edit(_["song_8"])
    yturl = f"https://www.youtube.com/watch?v={vidid}"
    with yt_dlp.YoutubeDL(get_ytdl_options({"quiet": True})) as ytdl:
        x = ytdl.extract_info(yturl, download=False)
    title = (x["title"]).title()
    title = re.sub("\W+", " ", title)
    thumb_image_path = await event.message.download_media()
    duration = x["duration"]
    if stype == "video":
        thumb_image_path = await event.message.download_media()
        try:
            file_path = await YouTube.download(
                yturl,
                mystic,
                songvideo=True,
                format_id=format_id,
                title=title,
            )
        except Exception as e:
            return await mystic.edit(_["song_9"].format(e))

        await mystic.edit(_["song_11"])
        try:
            await event.edit(
                file=file_path,
                message=title,
                thumb=thumb_image_path,
                supports_streaming=True,
            )
        except Exception:
            return await mystic.edit(_["song_10"])
        os.remove(file_path)
    elif stype == "audio":
        try:
            filename = await YouTube.download(
                yturl,
                mystic,
                songaudio=True,
                format_id=format_id,
                title=title,
            )
        except Exception as e:
            return await mystic.edit(_["song_9"].format(str(e)))
        await mystic.edit(_["song_11"])

        try:
            await event.edit(
                file=filename,
                message=title,
                thumb=thumb_image_path,
                attributes=[
                    DocumentAttributeAudio(
                        voice=False,
                        title=title,
                        performer=x["uploader"],
                    )
                ],
            )
        except Exception as e:
            return await mystic.edit(_["song_10"])
        os.remove(filename)
