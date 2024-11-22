#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import random

from telethon import events
import logging

import config
from config import (
    BANNED_USERS,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    SUPPORT_GROUP,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    lyrical,
)
from YukkiMusic import Apple, Spotify, YouTube, app
from YukkiMusic.core.call import Yukki
from YukkiMusic.misc import SUDOERS, db
from YukkiMusic.utils import seconds_to_min, time_to_seconds
from YukkiMusic.utils.channelplay import get_channeplayCB
from YukkiMusic.utils.database import (
    is_active_chat,
    is_music_playing,
    is_muted,
    is_nonadmin_chat,
    music_off,
    music_on,
    mute_off,
    mute_on,
    set_loop,
)
from YukkiMusic.utils.decorators import ActualAdminCB
from YukkiMusic.utils.decorators.language import languageCB
from YukkiMusic.utils.formatters import seconds_to_min
from YukkiMusic.utils.inline.play import (
    livestream_markup,
    panel_markup_1,
    panel_markup_2,
    panel_markup_3,
    slider_markup,
    stream_markup,
    telegram_markup,
)
from YukkiMusic.utils.stream.autoclear import auto_clean
from YukkiMusic.utils.stream.stream import stream
from YukkiMusic.utils.thumbnails import gen_thumb

wrong = {}

@app.on(events.CallbackQuery(pattern=r"PanelMarkup (\S+)\|(\S+)"))
@app.on(events.CallbackQuery(pattern=r"MainMarkup (\S+)\|(\S+)"))
@languageCB
async def handle_markup(event, _):
    await event.answer()
    videoid, chat_id = event.pattern_match.group(1), int(event.pattern_match.group(2))

    if "PanelMarkup" in event.data.decode("utf-8"):
        buttons = panel_markup_1(_, videoid, chat_id)
        value = False
    elif "MainMarkup" in event.data.decode("utf-8"):
        buttons = (
            telegram_markup(_, chat_id)
            if videoid == "None"
            else stream_markup(_, videoid, chat_id)
        )
        value = True

    try:
        await event.edit(buttons=buttons)
    except Exception:
        return

    if chat_id not in wrong:
        wrong[chat_id] = {}
    wrong[chat_id][event.message_id] = value

@app.on(events.CallbackQuery(pattern=r"Pages"))
@languageCB
async def pages(event, _):
    await event.answer()
    callback_data = event.data.decode("utf-8").strip()
    callback_request = callback_data.split(None, 1)[1]
    state, pages, videoid, chat = callback_request.split("|")
    chat_id = int(chat)
    pages = int(pages)

    if state == "Forw":
        buttons = (
            panel_markup_2(_, videoid, chat_id)
            if pages == 0
            else (
                panel_markup_1(_, videoid, chat_id)
                if pages == 2
                else panel_markup_3(_, videoid, chat_id)
            )
        )
    elif state == "Back":
        buttons = (
            panel_markup_3(_, videoid, chat_id)
            if pages == 0
            else (
                panel_markup_2(_, videoid, chat_id)
                if pages == 2
                else panel_markup_1(_, videoid, chat_id)
            )
        )

    try:
        await event.edit(buttons=buttons)
    except Exception:
        return


@app.on(
    events.CallbackQuery(
        pattern=r"ADMIN (Pause|Resume|Stop|End|Mute|Unmute|Loop|Shuffle|Skip|Seek)\|(\d+)"
    )
)
@languageCB
async def del_back_playlist(event, _):
    command, chat_id = (
        event.pattern_match.group(1),
        int(event.pattern_match.group(2)),
    )

    if not await is_active_chat(chat_id):
        return await event.answer(_["general_6"], alert=True)

    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    is_non_admin = await is_nonadmin_chat(event.chat_id)

    if not is_non_admin:
        if event.sender_id not in SUDOERS:
            admins = adminlist.get(event.chat_id)
            if not admins:
                return await event.answer(_["admin_18"], alert=True)
            else:
                if event.sender_id not in admins:
                    return await event.answer(_["admin_19"], alert=True)

    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await event.answer(_["admin_1"], alert=True)
        await event.answer()
        await music_off(chat_id)
        await Yukki.pause_stream(chat_id)
        await event.reply(_["admin_2"].format(mention))

    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await event.answer(_["admin_3"], alert=True)
        await event.answer()
        await music_on(chat_id)
        await Yukki.resume_stream(chat_id)
        await event.reply(_["admin_4"].format(mention))

    elif command == "Stop" or command == "End":
        try:
            check = db.get(chat_id)
            if check[0].get("mystic"):
                await check[0].get("mystic").delete()
        except Exception:
            pass
        await event.answer()
        await Yukki.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await event.reply(_["admin_9"].format(mention))

    elif command == "Mute":
        if await is_muted(chat_id):
            return await event.answer(_["admin_5"], alert=True)
        await event.answer()
        await mute_on(chat_id)
        await Yukki.mute_stream(chat_id)
        await event.reply(_["admin_6"].format(mention))

    elif command == "Unmute":
        if not await is_muted(chat_id):
            return await event.answer(_["admin_7"], alert=True)
        await event.answer()
        await mute_off(chat_id)
        await Yukki.unmute_stream(chat_id)
        await event.reply(_["admin_8"].format(mention))

    elif command == "Loop":
        await event.answer()
        await set_loop(chat_id, 3)
        await event.reply(_["admin_25"].format(mention, 3))

    elif command == "Shuffle":
        check = db.get(chat_id)
        if not check:
            return await event.answer(_["admin_21"], alert=True)
        try:
            popped = check.pop(0)
        except:
            return await event.answer(_["admin_22"], alert=True)
        if not check:
            check.insert(0, popped)
            return await event.answer(_["admin_22"], alert=True)
        await event.answer()
        random.shuffle(check)
        check.insert(0, popped)
        await event.reply(_["admin_23"].format(mention))

    elif command == "Skip":
        check = db.get(chat_id)
        txt = f"» Track skipped by {mention} !"
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                await auto_clean(popped)
            if not check:
                await event.edit(f"» Track skipped by  {mention} !")
                await event.reply(_["admin_10"].format(mention), link_preview=False)
                try:
                    return await Yukki.stop_stream(chat_id)
                except:
                    return
        except:
            try:
                await event.edit(f"» Track skipped by  {mention} !")
                await event.reply(_["admin_10"].format(mention), link_preview=False)
                return await Yukki.stop_stream(chat_id)
            except:
                return
        await event.answer()
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        duration_min = check[0]["dur"]
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await event.reply(_["admin_11"].format(title))
            try:
                await Yukki.skip_stream(chat_id, link, video=status)
            except Exception:
                return await event.reply(_["call_7"])
            button = telegram_markup(_, chat_id)
            img = await gen_thumb(videoid)
            run = await app.send_file(
                event.chat_id,
                file=img,
                caption=_["stream_1"].format(
                    user,
                    f"https://t.me/{app.username}?start=info_{videoid}",
                ),
                buttons=button,
                reply_to=event.message.id,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await event.edit(txt)
        elif "vid_" in queued:
            mystic = await event.reply(_["call_8"], link_preview=False)
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=status,
                )
            except:
                return await mystic.edit(_["call_7"])
            try:
                await Yukki.skip_stream(chat_id, file_path, video=status)
            except Exception:
                return await mystic.edit(_["call_7"])
            button = stream_markup(_, videoid, chat_id)
            img = await gen_thumb(videoid)
            run = await app.send_file(
                event.chat_id,
                file=img,
                caption=_["stream_1"].format(
                    title[:27],
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    duration_min,
                    user,
                ),
                buttons=button,
                reply_to=event.message.id,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await event.edit(txt)
            await mystic.delete()
        elif "index_" in queued:
            try:
                await Yukki.skip_stream(chat_id, videoid, video=status)
            except Exception:
                return await event.reply(_["call_7"])
            button = telegram_markup(_, chat_id)
            run = await app.send_file(
                event.chat_id,
                file=STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                buttons=button,
                reply_to=event.message.id,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await event.edit(txt)
        else:
            try:
                await Yukki.skip_stream(chat_id, queued, video=status)
            except Exception:
                return await event.reply(_["call_7"])
            if videoid == "telegram":
                button = telegram_markup(_, chat_id)
                run = await app.send_file(
                    event.chat_id,
                    file=(
                        TELEGRAM_AUDIO_URL
                        if str(streamtype) == "audio"
                        else TELEGRAM_VIDEO_URL
                    ),
                    caption=_["stream_1"].format(
                        title, SUPPORT_GROUP, check[0]["dur"], user
                    ),
                    buttons=button,
                    reply_to=event.message.id,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif videoid == "soundcloud":
                button = telegram_markup(_, chat_id)
                run = await app.send_file(
                    event.chat_id,
                    file=(
                        SOUNCLOUD_IMG_URL
                        if str(streamtype) == "audio"
                        else TELEGRAM_VIDEO_URL
                    ),
                    caption=_["stream_1"].format(
                        title, SUPPORT_GROUP, check[0]["dur"], user
                    ),
                    buttons=button,
                    reply_to=event.message.id,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif "saavn" in videoid:
                button = telegram_markup(_, chat_id)
                run = await app.send_file(
                    file=check[0]["thumb"],
                    caption=_["stream_1"].format(
                        title, SUPPORT_GROUP, check[0]["dur"], user
                    ),
                    buttons=button,
                    reply_to=event.message.id,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                button = stream_markup(_, videoid, chat_id)
                img = await gen_thumb(videoid)
                run = await app.send_file(
                    event.chat_id,
                    file=img,
                    caption=_["stream_1"].format(
                        title[:27],
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        duration_min,
                        user,
                    ),
                    buttons=button,
                    reply_to=event.message.id,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            await event.edit(txt)
    else:
        playing = db.get(chat_id)
        if not playing:
            return await event.answer(_["queue_2"], show_alert=True)
        duration_seconds = int(playing[0]["seconds"])
        if duration_seconds == 0:
            return await event.answer(_["admin_30"], show_alert=True)
        file_path = playing[0]["file"]
        if "index_" in file_path or "live_" in file_path:
            return await event.answer(_["admin_30"], show_alert=True)
        duration_played = int(playing[0]["played"])
        if int(command) in [1, 2]:
            duration_to_skip = 10
        else:
            duration_to_skip = 30
        duration = playing[0]["dur"]
        if int(command) in [1, 3]:
            if (duration_played - duration_to_skip) <= 10:
                bet = seconds_to_min(duration_played)
                return await event.answer(
                    f"Bot is unable to seek because duration exceeds.\n\nCurrently played:** {bet}** minutes out of **{duration}** minutes.",
                    show_alert=True,
                )
            to_seek = duration_played - duration_to_skip + 1
        else:
            if (duration_seconds - (duration_played + duration_to_skip)) <= 10:
                bet = seconds_to_min(duration_played)
                return await event.answer(
                    f"Bot is unable to seek because duration exceeds.\n\nCurrently played:** {bet}** minutes out of **{duration}** minutes.",
                    show_alert=True,
                )
            to_seek = duration_played + duration_to_skip + 1
        await event.answer()
        mystic = await event.reply(_["admin_32"])
        if "vid_" in file_path:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await mystic.edit(_["admin_30"])
        try:
            await Yukki.seek_stream(
                chat_id,
                file_path,
                seconds_to_min(to_seek),
                duration,
                playing[0]["streamtype"],
            )
        except:
            return await mystic.edit(_["admin_34"])
        if int(command) in [1, 3]:
            db[chat_id][0]["played"] -= duration_to_skip
        else:
            db[chat_id][0]["played"] += duration_to_skip
        string = _["admin_33"].format(seconds_to_min(to_seek))
        await mystic.edit(f"{string}\n\nChanges Done by: {mention} !")


@app.on(events.CallbackQuery(pattern=r"MusicStream (\S+)\|(\S+)\|(\S+)\|(\S+)\|(\S+)"))
@languageCB
async def play_music(event, _):
    callback_data = event.data.decode("utf-8").strip()
    _, videoid, user_id, mode, cplay, fplay = callback_data.split()
    if event.sender_id != int(user_id):
        return await event.answer(_["playcb_1"], alert=True)
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, event)
    except:
        return
    user_name = event.sender.first_name
    await event.delete()
    mystic = await event.reply(_["play_2"].format(channel) if channel else _["play_1"])
    try:
        details, track_id = await YouTube.track(videoid, True)
    except:
        return await mystic.edit(_["play_3"])
    if details["duration_min"]:
        duration_sec = time_to_seconds(details["duration_min"])
        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit(
                _["play_6"].format(config.DURATION_LIMIT_MIN, details["duration_min"])
            )
    else:
        buttons = livestream_markup(
            _,
            track_id,
            event.sender_id,
            mode,
            "c" if cplay == "c" else "g",
            "f" if fplay else "d",
        )
        return await mystic.edit(
            _["play_15"],
            buttons=buttons,
        )
    video = mode == "v"
    ffplay = fplay == "f"
    try:
        await stream(
            _,
            mystic,
            event.sender_id,
            details,
            chat_id,
            user_name,
            event.chat_id,
            video,
            streamtype="youtube",
            forceplay=ffplay,
        )
    except Exception as e:
        err = (
            str(e)
            if isinstance(e, AssistantErr)
            else _["general_3"].format(type(e).__name__)
        )
        return await mystic.edit_text(err)
    await mystic.delete()


@app.on(events.CallbackQuery(pattern="AnonymousAdmin"))
async def anonymous_check(event):
    await event.answer(
        "You are an anonymous admin\nRevert back to user to use me",
        alert=True,
    )


@app.on(
    events.CallbackQuery(
        pattern=r"YukkiPlaylists (\S+)\|(\S+)\|(\S+)\|(\S+)\|(\S+)\|(\S+)"
    )
)
@languageCB
async def play_playlists_command(event, _):
    callback_data = event.data.decode("utf-8").strip()
    _, videoid, user_id, ptype, mode, cplay, fplay = callback_data.split()
    if event.sender_id != int(user_id):
        return await event.answer(_["playcb_1"], alert=True)
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, event)
    except:
        return
    user_name = event.sender.first_name
    await event.delete()
    mystic = await event.message.reply(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    video = mode == "v"
    ffplay = fplay == "f"
    spotify = True
    if ptype == "yt":
        spotify = False
        try:
            result = await YouTube.playlist(
                videoid, config.PLAYLIST_FETCH_LIMIT, event.sender_id, True
            )
        except:
            return await mystic.edit(_["play_3"])
    elif ptype == "spplay":
        result, _ = await Spotify.playlist(videoid)
    elif ptype == "spalbum":
        result, _ = await Spotify.album(videoid)
    elif ptype == "spartist":
        result, _ = await Spotify.artist(videoid)
    elif ptype == "apple":
        result, _ = await Apple.playlist(videoid, True)
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
            spotify=spotify,
            forceplay=ffplay,
        )
    except Exception as e:
        err = (
            str(e)
            if isinstance(e, AssistantErr)
            else _["general_3"].format(type(e).__name__)
        )
        return await mystic.edit(err)
    await mystic.delete()


@app.on(
    events.CallbackQuery(pattern=r"slider (\S+)\|(\S+)\|(\S+)\|(\S+)\|(\S+)\|(\S+)")
)
@languageCB
async def slider_queries(event, _):
    callback_data = event.data.decode("utf-8").strip()
    _, what, rtype, query, user_id, cplay, fplay = callback_data.split("|")

    if event.sender_id != int(user_id):
        return await event.answer(_["playcb_1"], alert=True)

    query_type = (
        0 if rtype == "9" else (int(rtype) + 1 if what == "F" else int(rtype) - 1)
    )

    await event.answer(_["playcb_2"])

    title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)

    buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)

    await event.edit(
        file=thumbnail,
        message=_["play_11"].format(
            title.title(),
            duration_min,
        ),
        buttons=buttons,
    )


@app.on(events.CallbackQuery(pattern="close"))
async def close_menu(event):
    await event.delete()
    await event.answer()


@app.on(events.CallbackQuery(pattern="stop_downloading"))
@ActualAdminCB
async def stop_download(event, _):
    message_id = event.message.id
    task = lyrical.get(message_id)
    if not task:
        return await event.answer("Download Already Completed..", alert=True)
    if task.done() or task.cancelled():
        return await event.answer(
            "Downloading already Completed or Cancelled.",
            alert=True,
        )
    if not task.done():
        task.cancel()
        lyrical.pop(message_id, None)
        await event.answer("Downloading Cancelled", alert=True)
        return await event.edit_message_text(
            f"Downloading cancelled by {event.sender.mention}"
        )
    await event.answer("Failed to Recognise Task", alert=True)
