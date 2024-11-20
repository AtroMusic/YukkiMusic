#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import asyncio
import re
from telethon import events
from config import BANNED_USERS
from YukkiMusic import app
from YukkiMusic.utils.database import get_global_tops, get_particulars, get_userss
from YukkiMusic.utils.decorators import languageCB
from YukkiMusic.utils.inline.playlist import (
    botplaylist_markup,
    failed_top_markup,
    top_play_markup,
)
from YukkiMusic.utils.stream.stream import stream

loop = asyncio.get_running_loop()


def is_not_banned(event):
    return event.sender_id not in BANNED_USERS


@app.on(events.CallbackQuery(data=re.compile(b"get_playmarkup"), func=is_not_banned))
@languageCB
async def get_play_markup(event, _):
    try:
        await event.answer()
    except:
        pass
    buttons = botplaylist_markup(_)
    await event.edit(buttons=buttons)


@app.on(events.CallbackQuery(data=re.compile(b"get_top_playlists"), func=is_not_banned))
@languageCB
async def get_top_playlists(event, _):
    try:
        await event.answer()
    except:
        pass
    buttons = top_play_markup(_)
    await event.edit(buttons=buttons)


@app.on(events.CallbackQuery(data=re.compile(b"SERVERTOP (.+)"), func=is_not_banned))
@languageCB
async def server_to_play(event, _):
    chat_id = event.chat_id
    user_name = event.sender.first_name

    try:
        await event.answer()
    except:
        pass

    callback_data = event.data.decode("utf-8").strip()
    what = callback_data.split(None, 1)[1]
    mystic = await event.edit(
        _["tracks_1"].format(
            what,
            event.sender.first_name,
        )
    )

    upl = failed_top_markup(_)

    if what == "Global":
        stats = await get_global_tops()
    elif what == "Group":
        stats = await get_particulars(chat_id)
    elif what == "Personal":
        stats = await get_userss(event.sender_id)

    if not stats:
        return await mystic.edit(_["tracks_2"].format(what), buttons=upl)

    def get_stats():
        results = {}
        for i in stats:
            top_list = stats[i]["spot"]
            results[str(i)] = top_list
            list_arranged = dict(
                sorted(
                    results.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )
        if not results:
            return mystic.edit(_["tracks_2"].format(what), buttons=upl)

        details = []
        limit = 0
        for vidid, count in list_arranged.items():
            if vidid == "telegram":
                continue
            if limit == 10:
                break
            limit += 1
            details.append(vidid)

        if not details:
            return mystic.edit(_["tracks_2"].format(what), buttons=upl)
        return details

    try:
        details = await loop.run_in_executor(None, get_stats)
    except Exception:
        return

    try:
        await stream(
            _,
            mystic,
            event.sender_id,
            details,
            chat_id,
            user_name,
            event.chat_id,
            video=False,
            streamtype="playlist",
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
        await mystic.edit(str(err))
    else:
        await mystic.delete()
