#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the "MIT License Agreement".
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
import uvloop

uvloop.install()

import re
import sys
import datetime
import traceback
from typing import List, Union
from functools import wraps

from telethon import events
from telethon import TelegramClient

from telethon.errors import ChatSendMediaForbiddenError
from telethon.errors import ChatWriteForbiddenError
from telethon.errors import FloodWaitError
from telethon.errors import MessageIdInvalidError
from telethon.errors import MessageNotModifiedError

from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import DeleteChatUserRequest
from telethon.tl.functions.messages import ExportChatInviteRequest

from telethon.tl.types import User
from telethon.tl.types import BotCommand
from telethon.tl.types import BotCommandScopePeer
from telethon.tl.types import BotCommandScopePeerUser
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

    async def start(self):
        await super().start(bot_token=config.BOT_TOKEN)
        get_me = await self.get_me()
        self.username = get_me.username
        self.id = get_me.id
        self.name = get_me.first_name + " " + (get_me.last_name or "")
        self.mention = await self.create_mention(get_me)
        try:
            await self.send_message(
                config.LOG_GROUP_ID,
                message=f"<u><b>{await self.create_mention(get_me, True)} Bot Started :</b><u>\n\nId : <code>{self.id}</code>\nName : {self.name}\nUsername : @{self.username}",
                parse_mode="html",
            )
        except:
            LOGGER(__name__).error(
                "Bot has failed to access the log group. Make sure that you have added your bot to your log channel and promoted as admin!"
            )
            # sys.exit()
            
        if config.SET_CMDS == str(True):
            try:
            	await self._set_default_commands()
            except:
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

    def on_cmd(
        self,
        command: Union[str, List[str]],
        is_private: bool = None,
        is_group: bool = None,
        from_user: set = None,
        is_restricted: bool = False,
        edited: bool = False,
        capture_error: bool = True,
        **kwargs
    ):
        from_user = set() if from_user is None else from_user
        
        kwargs.get("incoming") = kwargs.get("incoming") or True
        
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
        	
        	@wraps(func)
        	async def wrapper(event):
        	    try:
        	        await func(event)
                except events.StopPropagation as e:
                    raise events.StopPropagation from e
                    
                except KeyboardInterrupt:
                	pass
                
                except FloodWaitError as e:
                    await event.delete()
                    await asyncio.sleep(e.seconds + 7)
                    
        	    except ChatWriteForbiddenError:
        	        try:
        	            await self.leave_chat(event.chat_id)
                    except:
                    	pass
                    
                except MessageIdInvalidError:
                	pass
                
                except MessageNotModifiedError:
                	pass
                
                except ChatSendMediaForbiddenError:
                	pass
                
                except Exception as e:
                	if capture_error:
                    	text= "**⚠️Error report :⚠️**\n\n"
                    	text+= f"**Date**: {(datetime.datetime.now()).strftime("%m/%d/%Y, %H:%M:%S")}\n"
                        text+= f"**Group Id** : {event.chat_id}\n"
                        text+= f"**User Id**: {event.sender_id}\n"
                        text+= "\n\n"
                        text+= f"Event Trigger:\n{str(event.text)}\n\n"
                        text+= f"Traceback info:\n{str(traceback.format_exc())}\n\n"
                        text+= f"Error text:\n{str(sys.exc_info()[1])}"
                        await self.send_message(config.LOG_GROUP_ID, text)
                        
                    LOGGER(__name__).error("Error\n\n", exc_info=True)
                    
            if edited:
            	self.add_event_handler(
                    wrapper,
                    events.MessageEdited(
                        pattern=pattern,
                        func=check_event,
                        **kwargs
                    )
                    
            self.add_event_handler(
                wrapper,
                events.NewMessage(
                    pattern=pattern,
                    func=check_event,
                    **kwargs
                )
                
            return wrapper

        return decorator
        

    async def _set_default_commands(self):
        private_commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get the help menu"),
            BotCommand("ping", "Check if the bot is alive or dead"),
        ]
        group_commands = [BotCommand("play", "Start playing requested song")]
        admin_commands = [
            BotCommand("play", "Start playing requested song"),
            BotCommand("skip", "Move to next track in queue"),
            BotCommand("pause", "Pause the current playing song"),
            BotCommand("reboot", "Reboot the bot for group"),
            BotCommand("resume", "Resume the paused song"),
            BotCommand("end", "Clear the queue and leave voice chat"),
            BotCommand("shuffle", "Randomly shuffle the queued playlist"),
            BotCommand("playmode", "Change the default playmode for your chat"),
            BotCommand("settings", "Open bot settings for your chat"),
        ]
        owner_commands = [
            BotCommand("update", "Update the bot"),
            BotCommand("restart", "Restart the bot"),
            BotCommand("logs", "Get logs"),
            BotCommand("export", "Export all data of mongodb"),
            BotCommand("import", "Import all data in mongodb"),
            BotCommand("addsudo", "Add a user as a sudoer"),
            BotCommand("delsudo", "Remove a user from sudoers"),
            BotCommand("sudolist", "List all sudo users"),
            BotCommand("log", "Get the bot logs"),
            BotCommand("getvar", "Get a specific environment variable"),
            BotCommand("delvar", "Delete a specific environment variable"),
            BotCommand("setvar", "Set a specific environment variable"),
            BotCommand("usage", "Get dyno usage information"),
            BotCommand("maintenance", "Enable or disable maintenance mode"),
            BotCommand("logger", "Enable or disable logging"),
            BotCommand("block", "Block a user"),
            BotCommand("unblock", "Unblock a user"),
            BotCommand("blacklist", "Blacklist a chat"),
            BotCommand("whitelist", "Whitelist a chat"),
            BotCommand("blacklisted", "List all blacklisted chats"),
            BotCommand("autoend", "Enable or disable auto end for streams"),
            BotCommand("reboot", "Reboot the bot for group"),
            BotCommand("restart", "Restart the bot"),
        ]
        async def set_bot_commands(command: list, scope):
        	await self(
                    SetBotCommandsRequest(
                        scope=scope,
                        commands=command,
                        lang_code="",
                    )
                )
                
        await set_bot_commands(
            private_commands, scope=BotCommandScopeUsers()
        )
        
        await set_bot_commands(
            group_commands, scope=BotCommandScopeChats()
        )
        await set_bot_commands(
            admin_commands, scope=BotCommandScopeChatAdmins(),
        )

        for owner_id in config.OWNER_ID:
            try:
                await set_bot_commands(
                    owner_commands,
                    scope=BotCommandScopePeerUser(
                        peer=await self.get_entity(config.LOG_GROUP_ID), user_id=await self.get_entity(owner_id)
                      )
               )
                await set_bot_commands(
                    private_commands + owner_commands, scope=BotCommandScopePeer(await self.get_entity(owner_id))
                )
            except Exception:
                pass

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
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        user_id = user.id
        if html:
            mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
        else:
            mention = f"[{user_name}](tg://user?id={user_id})"
        return mention