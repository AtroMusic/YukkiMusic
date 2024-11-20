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

from pyrogram.errors import (
    InviteRequestSent,
    ChannelsTooMuch,
    UserAlreadyParticipant,
    FloodWait,
)

from telethon.errors import ChatAdminRequiredError, UserNotParticipantError
from telethon.tl.types import User, ChannelParticipantBanned, ChannelParticipantLeft
from telethon.tl.functions.messages import HideChatJoinRequestRequest

from config import PLAYLIST_IMG_URL, PRIVATE_BOT_MODE
from config import SUPPORT_GROUP as SUPPORT_CHAT
from config import adminlist

from strings import get_string

from YukkiMusic import YouTube, app
from YukkiMusic.core.call import Yukki
from YukkiMusic.core.userbot import assistants
from YukkiMusic.misc import SUDOERS
from YukkiMusic.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
    is_active_chat,
    is_commanddelete_on,
    is_maintenance,
    is_served_private_chat,
    set_assistant,
)
from YukkiMusic.utils.inline import botplaylist_markup

links = {}


async def join_chat(event, chat_id, _, myu, attempts=1):
    max_attempts = len(assistants) - 1  # Set the maximum number of attempts
    userbot = await get_assistant(chat_id)
    chat = await event.get_chat()

    if chat_id in links:
        invitelink = links[chat_id]
    else:
        if chat.username:
            invitelink = chat.username
            try:
                await userbot.resolve_peer(invitelink)
            except:
                pass
        else:
            try:
                invitelink = await app.export_invite_link(event.chat_id)
            except ChatAdminRequiredError:
                return await myu.edit(_["call_1"])
            except Exception as e:
                return await myu.edit(_["call_3"].format(app.mention, type(e).__name__))

        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace("https://t.me/+", "https://t.me/joinchat/")
        links[chat_id] = invitelink

    try:
        await asyncio.sleep(1)
        await userbot.join_chat(invitelink)
    except InviteRequestSent:
        try:
            await app(
                HideChatJoinRequestRequest(
                    peer=chat_id, user_id=userbot.id, approved=True
                )
            )
        except Exception as e:
            return await myu.edit(_["call_3"].format(type(e).__name__))
        await asyncio.sleep(1)
        await myu.edit(_["call_6"].format(app.mention))
    except UserAlreadyParticipant:
        pass
    except ChannelsTooMuch:
        if attempts <= max_attempts:
            userbot = await set_assistant(chat_id)
            return await join_chat(event, chat_id, _, myu, attempts + 1)
        else:
            return await myu.edit(_["call_9"].format(SUPPORT_CHAT))
    except FloodWait as e:
        time = e.value
        if time < 20:
            await asyncio.sleep(time)
            return await join_chat(event, chat_id, _, myu, attempts + 1)
        else:
            if attempts <= max_attempts:
                userbot = await set_assistant(chat_id)
                return await join_chat(event, chat_id, _, myu, attempts + 1)

            return await myu.edit(_["call_10"].format(time))
    except Exception as e:
        return await myu.edit(_["call_3"].format(type(e).__name__))

    try:
        await myu.delete()
    except:
        pass


def PlayWrapper(command):
    async def wrapper(event):
        language = await get_lang(event.chat_id)
        _ = get_string(language)
        sender = await event.get_sender()
        if not isinstance(sender, User):
            upl = [
                [
                    Button.inline(
                        text="How to Fix ?",
                        data="AnonymousAdmin",
                    ),
                ]
            ]
            return await event.reply(_["general_4"], buttons=upl)

        if await is_maintenance() is False:
            if event.sender_id not in SUDOERS:
                return

        if PRIVATE_BOT_MODE == str(True):
            if not await is_served_private_chat(event.chat_id):
                await event.reply(
                    "**PRIVATE MUSIC BOT**\n\nOnly For Authorized chats from the owner ask my owner to allow your chat first."
                )
                return await app.leave_chat(event.chat_id)
        if await is_commanddelete_on(event.chat_id):
            try:
                await event.delete()
            except:
                pass

        audio_telegram, video_telegram = None, None
        if event.message.is_reply:
            r_msg = await event.get_reply_message()

            audio_telegram = (r_msg.audio or r_msg.voice) if r_msg else None
            video_telegram = (r_msg.video or r_msg.document) if r_msg else None


        url = await YouTube.url(event)
        if audio_telegram is None and video_telegram is None and url is None:
            if len(event.text.split()) < 2:
                if "stream" in event.text.split():
                    return await event.reply(_["str_1"])
                buttons = botplaylist_markup(_)
                return await app.send_file(
                    event.chat_id,
                    file=PLAYLIST_IMG_URL,
                    caption=_["playlist_1"],
                    buttons=buttons,
                )
        if event.text.split()[0][0] == "c":
            chat_id = await get_cmode(event.chat_id)
            if chat_id is None:
                return await event.reply(_["setting_12"])
            try:
                chat = await app.get_entity(chat_id)
            except:
                return await event.reply(_["cplay_4"])
            channel = chat.title
        else:
            chat_id = event.chat_id
            channel = None
        try:
            is_call_active = (await app.get_entity(chat_id)).call_active
            if not is_call_active:
                return await event.reply(
                    "**No active video chat found **\n\nPlease make sure you started the voicechat."
                )
        except Exception:
            pass

        playmode = await get_playmode(event.chat_id)
        playty = await get_playtype(event.chat_id)
        if playty != "Everyone":
            if event.sender_id not in SUDOERS:
                admins = adminlist.get(event.chat_id)
                if not admins:
                    return await event.reply(_["admin_18"])
                else:
                    if event.sender_id not in admins:
                        return await event.reply(_["play_4"])
        if event.text.split()[0][0] == "v":
            video = True
        else:
            if "-v" in event.text:
                video = True
            else:
                video = True if event.text.split()[0][1] == "v" else None
        if event.text.split()[0][-1] == "e":
            if not await is_active_chat(chat_id):
                return await event.reply(_["play_18"])
            fplay = True
        else:
            fplay = None

        if await is_active_chat(chat_id):
            userbot = await get_assistant(event.chat_id)
            # Getting all members id that in voicechat
            call_participants_id = [
                member.chat.id
                async for member in userbot.get_call_members(chat_id)
                if member.chat
            ]
            # Checking if assistant id not in list so clear queues and remove active voice chat and process

            if not call_participants_id or userbot.id not in call_participants_id:
                await Yukki.stop_stream(chat_id)

        else:
            userbot = await get_assistant(event.chat_id)
            try:
                try:
                    member = await app.get_participant(chat_id, userbot.id)
                except ChatAdminRequiredError:
                    return await event.reply(_["call_1"])
                if isinstance(
                    member, (ChannelParticipantLeft, ChannelParticipantBanned)
                ):
                    try:
                        await app.edit_permissions(chat_id, userbot.id)
                    except:
                        return await event.reply(
                            message=_["call_2"].format(userbot.username, userbot.id),
                        )
            except UserNotParticipantError:
                myu = await event.reply(_["call_5"])
                await join_chat(event, chat_id, _, myu)

        return await command(
            event,
            _,
            chat_id,
            video,
            channel,
            playmode,
            url,
            fplay,
        )

    return wrapper
