#
# Copyright (C) 2024 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#
from enum import Enum, auto

from .Apple import Apple
from .Carbon import Carbon
from .JioSavan import Saavn
from .Resso import Resso
from .Soundcloud import SoundCloud
from .Spotify import Spotify
from .Telegram import Telegram
from .Youtube import YouTube

class SourceType(Enum):
    APPLE = auto()
    RESSO = auto()
    SAAVN = auto()
    SOUNDCLOUD = auto()
    SPOTIFY = auto()
    TELEGRAM = auto()
    YOUTUBE = auto()
    
    
class PlaTForms:
    def __init__(self):
        self.apple = Apple()
        self.carbon = Carbon()
        self.saavn = Saavn()
        self.resso = Resso()
        self.soundcloud = SoundCloud()
        self.spotify = Spotify()
        self.telegram = Telegram()
        self.youtube = YouTube()
        
    async def info(type: SourceType, *, **kwargs) -> dict: # todo implement all classes and there info function in this function using SourceType and **kwargs
        pass
        
    async def download(type: SourceType, *, **kwargs) -> dict: #todo implement all downlod methdos in this download
        pass

    
