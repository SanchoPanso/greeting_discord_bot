import discord
from discord.ext import commands
from discord import VoiceClient
import asyncio
import os

import src.config as cfg
from src.connection import connect, disconnect
from src.mode_manager import ModeManager
from src.greeting import Greeter
import src.cogs as cogs


class GreetingBot(commands.Bot):
    def __init__(self):

        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix=cfg.prefix, intents=intents)
        self.gr = Greeter()
        self.mm = ModeManager()

        self.add_cog(cogs.Base(self))
        self.add_cog(cogs.Mode(self, self.mm))
        self.add_cog(cogs.Greet(self, self.gr))

    async def play_greeting(self, voice_client: VoiceClient):
        while voice_client.is_playing():
            await asyncio.sleep(1)

        if os.name == 'nt':
            voice_client.play(discord.FFmpegPCMAudio(executable=cfg.executable_path,
                                                     source=self.gr.greet_path))
        elif os.name == 'posix':
            voice_client.play(discord.FFmpegPCMAudio(source=self.gr.greet_path))

        while voice_client.is_playing():
            await asyncio.sleep(1)

    async def on_ready(self):
        print('Ready!')
        print(f"OS is {os.name}")

    async def on_voice_state_update(self, member, before, after):

        if self.mm.bot_must_connect_and_play(self, member, before, after):

            self.gr.prepare_file_for_playing(after, member)
            voice_client = await connect(self, after.channel)
            await self.play_greeting(voice_client)

        if self.mm.bot_must_disconnect(before, after):
            await disconnect(self)


if __name__ == '__main__':
    pass
