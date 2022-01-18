import discord
from discord.ext import commands
from discord import VoiceClient
import asyncio
import os
from os import getenv
from sys import exit

from config import settings, paths
from connection import connect, disconnect, is_connected
from mode_manager_module import ModeManager
from greeting import Greeter
import cogs

# greeting = Greeting()
# mode_manager = ModeManager()

intents = discord.Intents.default()
intents.members = True


class GreetingBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=settings['prefix'], intents=intents)
        self.greeting = Greeter()
        self.mode_manager = ModeManager()

        self.add_cog(cogs.Base(self))
        self.add_cog(cogs.Mode(self, self.mode_manager))
        self.add_cog(cogs.Greet(self, self.greeting))

    def play_greeting(self, voice_client: VoiceClient):
        while voice_client.is_playing():
            await asyncio.sleep(1)

        if os.name == 'nt':
            voice_client.play(discord.FFmpegPCMAudio(executable=paths['executable_path'],
                                                     source=self.greeting.greet_path))
        elif os.name == 'posix':
            voice_client.play(discord.FFmpegPCMAudio(source=self.greeting.greet_path))

        while voice_client.is_playing():
            await asyncio.sleep(1)

    async def on_ready(self):
        print('Ready!')
        print(f"OS is {os.name}")

    async def on_voice_state_update(self, member, before, after):

        if self.mode_manager.bot_must_connect_and_play(self, member, before, after):

            self.greeting.prepare_file_for_playing(after, member)
            voice_client = await connect(self, after.channel)
            self.play_greeting(voice_client)

        if self.mode_manager.bot_must_disconnect(before, after):
            await disconnect(self)

        # if self.mode_manager.mode == 1:
        #
        #     cond1 = before.channel is not after.channel
        #     cond2 = after.channel is not None
        #     cond3 = member.id != self.user.id
        #     cond4 = after.channel.guild.me.permissions_in(after.channel).connect if cond2 else False
        #
        #     all_conditions_are_true = cond1 and cond2 and cond3 and cond4
        #
        #     if all_conditions_are_true:
        #         self.greeting.prepare_file_for_playing(after, member)
        #         voice_client = await connect(self, after.channel)
        #         self.play_greeting(voice_client)
        #         await disconnect(self)
        #
        # elif self.mode_manager.mode == 2:
        #     if self.mode_manager.voice_channel_for_mode_2 is not None and member.id != self.user.id:
        #
        #         if before.channel != self.mode_manager.voice_channel_for_mode_2:
        #             if after.channel == self.mode_manager.voice_channel_for_mode_2:
        #
        #                 self.greeting.prepare_file_for_playing(after, member)
        #
        #                 voice_client = await connect(self, after.channel)
        #                 self.play_greeting(voice_client)
        #
        #         if before.channel == self.mode_manager.voice_channel_for_mode_2:
        #             if after.channel != self.mode_manager.voice_channel_for_mode_2:
        #                 if is_connected(self):
        #                     voice_client = self.voice_clients[0]
        #                     if len(self.mode_manager.voice_channel_for_mode_2.members) == 1:
        #                         await voice_client.disconnect()


if __name__ == '__main__':
    pass
