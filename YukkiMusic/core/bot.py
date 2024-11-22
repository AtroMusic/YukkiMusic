#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import uvloop

uvloop.install()

import re
import sys
from typing import List, Union


from telethon import events
from telethon import TelegramClient

from telethon.errors import ChatWriteForbiddenError
from telethon.errors import FloodWaitError
from telethon.errors import MessageIdInvalidError

from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatUserRequest
from telethon.tl.functions.messages import ExportChatInviteRequest

from telethon.tl.types import User
from telethon.tl.types import BotCommand
from telethon.tl.types import BotCommandScopeUsers
from telethon.tl.types import BotCommandScopeChats
from telethon.tl.types import BotCommandScopeChatAdmins
from telethon.tl.types import ChannelParticipant
from telethon.tl.types import InputUserSelf
from telethon.tl.types import PeerChannel
from telethon.tl.types import PeerChat


import config

from ..logging import LOGGER


class YukkiBot(TelegramClient):
    def __init__(self):
        LOGGER(__name__).info(f"Starting Bot")
        super().__init__(
            "YukkiMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            flood_sleep_threshold=240,
        )

    async def edit_message(self, *args, **kwargs):
        try:
            return await super().edit_message(*args, **kwargs)
        except FloodWaitError as e:
            time = int(e.seconds)
            await asyncio.sleep(time)
            if time < 25:
                return await self.edit_message_text(self, *args, **kwargs)
        except MessageIdInvalidError:
            pass

    async def send_message(self, *args, **kwargs):
        if kwargs.get("send_direct", False):
            kwargs.pop("send_direct", None)
            return await super().send_message(*args, **kwargs)

        try:
            return await super().send_message(*args, **kwargs)
        except FloodWaitError as e:
            time = int(e.seconds)
            await asyncio.sleep(time)
            if time < 25:
                return await self.send_message(self, *args, **kwargs)
        except ChatWriteForbiddenError:
            chat_id = kwargs.get("chat_id") or args[0]
            if chat_id:
                await self.leave_chat(chat_id)

    async def send_file(self, *args, **kwargs):
        try:
            return await super().send_file(*args, **kwargs)
        except FloodWaitError as e:
            time = int(e.seconds)
            await asyncio.sleep(time)
            if time < 25:
                return await self.send_file(self, *args, **kwargs)

    async def start(self):
        await super().start(bot_token=config.BOT_TOKEN)
        self.parse_mode = "markdown"
        self.get_me = await self.get_me()
        self.username = get_me.username
        self.id = get_me.id
        self.name = get_me.first_name + " " + (get_me.last_name or "")
        self.mention = await self.create_mention(get_me)
        try:
            await self.send_message(
                config.LOG_GROUP_ID,
                message=f"<u><b>{await self.create_mention(self.get_me, html = True)} Bot Started :</b><u>\n\nId : <code>{self.id}</code>\nName : {self.name}\nUsername : @{self.username}",
                parse_mode="html",
            )
        except:
            LOGGER(__name__).error(
                "Bot has failed to access the log group. Make sure that you have added your bot to your log channel and promoted as admin!"
            )
            # sys.exit()
        if config.SET_CMDS == str(True):
            try:
                await self(
                    SetBotCommandsRequest(
                        scope=BotCommandScopeUsers(),
                        commands=[
                            BotCommand("start", "Start the bot"),
                            BotCommand("help", "Get the help menu"),
                            BotCommand("ping", "Check if the bot is alive or dead"),
                        ],
                        lang_code="",
                    )
                )
                await self(
                    BotCommandScopeChats(
                        commands=[
                            BotCommand("play", "Start playing requested song"),
                        ],
                        lang_code="",
                        scope=BotCommandScopeChats(),
                    )
                )
                await self(
                    BotCommandScopeChats(
                        commands=[
                            BotCommand("play", "Start playing requested song"),
                            BotCommand("skip", "Move to next track in queue"),
                            BotCommand("pause", "Pause the current playing song"),
                            BotCommand("resume", "Resume the paused song"),
                            BotCommand("end", "Clear the queue and leave voicechat"),
                            BotCommand(
                                "shuffle", "Randomly shuffles the queued playlist."
                            ),
                            BotCommand(
                                "playmode",
                                "Allows you to change the default playmode for your chat",
                            ),
                            BotCommand(
                                "settings",
                                "Open the settings of the music bot for your chat.",
                            ),
                        ],
                        lang_code="",
                        scope=BotCommandScopeChatAdmins(),
                    )
                )
            except:
                pass
        else:
            pass
        try:
            a = await self.get_permissions(config.LOG_GROUP_ID, self.id)
            if not a.is_admin:
                LOGGER(__name__).error("Please promote bot as admin in logger group")
                sys.exit()
        except ValueError:
            LOGGER(__name__).error("Please promote bot as admin in logger group")
            sys.exit()
        except Exception:
            pass

        LOGGER(__name__).info(f"MusicBot started as {self.name}")

    def on_message(
        self,
        command: Union[str, List[str]],
        is_private: bool = None,
        is_group: bool = None,
        from_user: set = None,
        is_restricted: bool = False,
        incoming: bool = True,
        outgoing: bool = None,
    ):
        from_user = set() if from_user is None else from_user

        if isinstance(command, str):
            command = [command]

        command = "|".join(command)
        pattern = re.compile(rf"^[\/!]({command})(?:\s|$)", re.IGNORECASE)

        def check_event(event):
            in_ids = event.chat_id in from_user or event.sender_id in from_user
            if is_restricted:
                if in_ids:
                    return False
            else:
                if not in_ids and from_user:
                    return False
            if is_private is None and is_group is None:
                return True
            if is_private and event.is_private:
                return True
            if is_group and event.is_group:
                return True
            return False

        def decorator(func):
            self.add_event_handler(
                func,
                events.NewMessage(
                    pattern=pattern,
                    incoming=incoming,
                    outgoing=outgoing,
                    func=check_event,
                ),
            )
            return func

        return decorator

    async def get_participant(self, chat_id, user_id) -> ChannelParticipant:
        result = await self(GetParticipantRequest(channel=chat_id, participant=user_id))
        return result.participant

    async def export_invite_link(self, chat_id) -> str:
        result = await self(ExportChatInviteRequest(chat_id))
        return result.link

    async def leave_chat(self, chat_id):
        entity = await self.get_entity(chat_id)

        if isinstance(entity, PeerChannel) or (
            hasattr(entity, "megagroup") and entity.megagroup
        ):
            await self(LeaveChannelRequest(entity))
        elif isinstance(entity, PeerChat) or hasattr(entity, "chat_id"):
            await self(DeleteChatUserRequest(entity.id, InputUserSelf()))

    async def create_mention(self, user: User, html: bool = False) -> str:
        """
        Create a markdown mention for a given Telethon user.

        Args:
            user (User): A Telethon User object containing the user's details.
            html (bool): If html is True return the html mention.

        Returns:
            str: A markdown formatted mention.
        """
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        user_id = user.id
        if html:
            mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
        else:
            mention = f"[{user_name}](tg://user?id={user_id})"
        return mention