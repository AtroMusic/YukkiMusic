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
from random import randint

from telethon import events

from pykeyboard import InlineKeyboard

from config import BANNED_USERS, SERVER_PLAYLIST_LIMIT
from strings import get_command
from YukkiMusic import Carbon, YouTube, app
from YukkiMusic.utils.database import (
    delete_playlist,
    get_playlist,
    get_playlist_names,
    save_playlist,
)
from YukkiMusic.utils.decorators import language, languageCB
from YukkiMusic.utils.decorators.play import botplaylist_markup
from YukkiMusic.utils.inline.playlist import get_playlist_markup, warning_markup
from YukkiMusic.utils.pastebin import Yukkibin
from YukkiMusic.utils.stream.stream import stream

ADD_PLAYLIST_COMMAND = get_command("ADD_PLAYLIST_COMMAND")
PLAY_PLAYLIST_COMMAND = get_command("PLAY_PLAYLIST_COMMAND")
PLAYLIST_COMMAND = get_command("PLAYLIST_COMMAND")
DELETE_PLAYLIST_COMMAND = get_command("DELETE_PLAYLIST_COMMAND")


@app.on_message(
    command=PLAYLIST_COMMAND,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@language
async def check_playlist(event, _):
    _playlist = await get_playlist_names(event.sender_id)
    if _playlist:
        get = await event.reply(_["playlist_2"])
    else:
        return await event.reply(_["playlist_3"])
    msg = _["playlist_4"]
    count = 0
    for ptlist in _playlist:
        _note = await get_playlist(event.sender_id, ptlist)
        title = _note["title"]
        title = title.title()
        duration = _note["duration"]
        count += 1
        msg += f"\n\n{count}- {title[:70]}\n"
        msg += _["playlist_5"].format(duration)
    link = await Yukkibin(msg)
    lines = msg.count("\n")
    if lines >= 17:
        car = os.linesep.join(msg.split(os.linesep)[:17])
    else:
        car = msg
    carbon = await Carbon.generate(car, randint(100, 10000000000))
    await get.delete()
    await app.send_photo(
        event.chat_id,
        carbon,
        caption=_["playlist_15"].format(link),
        reply_to=event.sender_id,
    )


async def get_keyboard(_, user_id):
    keyboard = InlineKeyboard(row_width=5)
    _playlist = await get_playlist_names(user_id)
    count = len(_playlist)
    for x in _playlist:
        _note = await get_playlist(user_id, x)
        title = _note["title"]
        title = title.title()
        keyboard.row(
            Button.inline(
                text=title,
                data=f"del_playlist {x}",
            )
        )
    keyboard.row(
        Button.inline(
            text=_["PL_B_5"],
            data=f"delete_warning",
        ),
        Button.inline(text=_["CLOSE_BUTTON"], data=f"close"),
    )
    return keyboard, count


@app.on_message(
    command=DELETE_PLAYLIST_COMMAND,
    is_group=True,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@language
async def del_group_message(event, _):
    upl = [
        [
            Button.url(
                text=_["PL_B_6"],
                url=f"https://t.me/{app.username}?start=delplaylists",
            ),
        ]
    ]
    await event.reply(_["playlist_6"], buttons=upl)


@app.on_message(
    command=DELETE_PLAYLIST_COMMAND,
    is_private=True,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@language
async def del_plist_msg(event, _):
    _playlist = await get_playlist_names(event.sender_id)
    if _playlist:
        get = await event.reply(_["playlist_2"])
    else:
        return await event.reply(_["playlist_3"])
    keyboard, count = await get_keyboard(_, event.sender_id)
    await get.edit(_["playlist_7"].format(count), buttons=keyboard)


@app.on(
    events.CallbackQuery(
        pattern=re.compile(b"play_playlist (.+)"),
        func=lambda e: e.sender_id not in BANNED_USERS,
    )
)
@languageCB
async def play_playlist(event, _):
    mode = event.data_match.group(1).decode("utf-8")
    user_id = event.sender_id
    _playlist = await get_playlist_names(user_id)
    if not _playlist:
        try:
            return await event.answer(
                _["playlist_3"],
                alert=True,
            )
        except:
            return
    chat_id = event.chat_id
    sender = await event.get_sender()
    user_name = sender.first_name
    await event.delete()
    result = []
    try:
        await event.answer()
    except:
        pass
    video = True if mode == "v" else None
    mystic = await event.reply(_["play_1"])
    for vidids in _playlist:
        result.append(vidids)
    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            event.chat_id,
            video,
            streamtype="playlist",
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
        return await mystic.edit(str(err))
    return await mystic.delete()


@app.on_message(
    command=PLAY_PLAYLIST_COMMAND,
    is_group=True,
    from_user=BANNED_USERS,
    is_restricted=True,
)
@languageCB
async def play_playlist_command(event, _):
    mode = event.message.text.split()[0][0]
    user_id = event.sender_id
    _playlist = await get_playlist_names(user_id)
    if not _playlist:
        try:
            return await message.reply(
                _["playlist_3"],
                quote=True,
            )
        except:
            return

    chat_id = event.chat_id
    user_name = (await event.get_sender()).first_name

    try:
        await event.delete()
    except:
        pass

    result = []
    video = True if mode == "v" else None
    mystic = await event.reply(_["play_1"])

    for vidids in _playlist:
        result.append(vidids)

    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            event.chat_id,
            video,
            streamtype="playlist",
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
        return await mystic.edit(str(err))

    return await mystic.delete()


@app.on(
    events.CallbackQuery(
        pattern=re.compile(b"add_playlist (.+)"),
        func=lambda e: e.sender_id not in BANNED_USERS,
    )
)
@languageCB
async def add_playlist(event, _):
    video_id = event.data_match.group(1).decode("utf-8")
    user_id = event.sender_id
    _check = await get_playlist(user_id, videoid)
    if _check:
        try:
            return await event.answer(_["playlist_8"], alert=True)
        except:
            return
    _count = await get_playlist_names(user_id)
    count = len(_count)
    if count == SERVER_PLAYLIST_LIMIT:
        try:
            return await event.answer(
                _["playlist_9"].format(SERVER_PLAYLIST_LIMIT),
                alert=True,
            )
        except:
            return
    (
        title,
        duration_min,
        duration_sec,
        thumbnail,
        vidid,
    ) = await YouTube.details(videoid, True)
    title = (title[:50]).title()
    plist = {
        "videoid": vidid,
        "title": title,
        "duration": duration_min,
    }
    await save_playlist(user_id, videoid, plist)
    try:
        title = (title[:30]).title()
        return await event.answer(_["playlist_10"].format(title), alert=True)
    except:
        return


@app.on(
    events.CallbackQuery(
        pattern=re.compile(b"del_playlist (.+)"),
        func=lambda e: e.sender_id not in BANNED_USERS,
    )
)
@languageCB
async def del_plist(event, _):
    video_id = event.data_match.group(1).decode("utf-8")
    user_id = event.sender_id
    deleted = await delete_playlist(user_id, videoid)
    if deleted:
        try:
            await event.answer(_["playlist_11"], alert=True)
        except:
            pass
    else:
        try:
            return await event.answer(_["playlist_12"], alert=True)
        except:
            return
    keyboard, count = await get_keyboard(_, user_id)
    return await event.edit(buttons=keyboard)


@app.on(
    events.CallbackQuery(
        pattern=b"delete_whole_playlist", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def del_whole_playlist(event, _):
    _playlist = await get_playlist_names(event.sender_id)
    for x in _playlist:
        await event.answer(_["playlist_25"], alert=True)
        await delete_playlist(event.sender_id, x)
    return await event.edit(_["playlist_13"])


@app.on(
    events.CallbackQuery(
        pattern=b"get_playlist_playmode", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def get_playlist_playmode_(event, _):
    try:
        await event.answer()
    except:
        pass
    buttons = get_playlist_markup(_)
    await event.edit(buttons=buttons)


@app.on(
    events.CallbackQuery(
        pattern=b"home_play", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def home_play_(event, _):
    try:
        await event.answer()
    except:
        pass
    buttons = botplaylist_markup(_)
    return await event.edit(buttons=buttons)


@app.on(
    events.CallbackQuery(
        pattern=b"delete_warning", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def delete_warning_message(event, _):
    try:
        await event.answer()
    except:
        pass
    upl = warning_markup(_)
    return await event.edit(_["playlist_14"], buttons=upl)


@app.on(
    events.CallbackQuery(
        pattern=b"del_back_playlist", func=lambda e: e.sender_id not in BANNED_USERS
    )
)
@languageCB
async def del_back_playlist(event, _):
    user_id = event.sender_id
    _playlist = await get_playlist_names(user_id)
    if _playlist:
        try:
            await event.answer(_["playlist_2"], alert=True)
        except:
            pass
    else:
        try:
            return await event.answer(_["playlist_3"], alert=True)
        except:
            return
    keyboard, count = await get_keyboard(_, user_id)
    return await event.edit(_["playlist_7"].format(count), buttons=keyboard)
