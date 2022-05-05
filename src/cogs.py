import discord
from discord.ext import commands
import asyncio
import os

import src.connection as connection
from src.mode_manager import ModeManager
from src.greeting import Greeter
import src.config as cfg


class Base(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """
        Send "Hello World!"
        """
        await ctx.channel.send('**Hello World!**')

    @commands.command()
    async def connect(self, ctx: commands.Context, number: str):
        """
        Connect to the voice channel, which is placed in the guild where this command is recalled
        and which has required number
        """

        if not number.isdigit():
            await ctx.channel.send('Неправильный аргумент')  # 1
            return

        number = int(number)

        if not (1 <= number <= len(ctx.guild.voice_channels)):
            await ctx.channel.send('Неправильный аргумент')  # 2
            return

        new_channel = ctx.guild.voice_channels[number - 1]
        await connection.connect(self.bot, new_channel)

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        """
        disconnect from any voice channel
        """
        await ctx.guild.change_voice_state(channel=None,
                                           self_mute=False,
                                           self_deaf=False)

    @commands.command()
    async def voice_members_info(self, ctx: commands.Context):
        """
        Send info about members in all voice channels
        """
        for channel in ctx.guild.voice_channels:
            await ctx.channel.send(channel)
            for member in channel.members:
                await ctx.channel.send(member)

    @commands.command()
    async def members_info(self, ctx: commands.Context):
        """
        Send info about members
        """
        members = ctx.guild.members
        await ctx.channel.send(members)

    @commands.command()
    async def members_brief_info(self, ctx: commands.Context):
        """
        Send brief info about members
        """
        members = ctx.guild.members
        result = ''
        for i in range(len(members)):
            result += 'name: ' + members[i].name + ', '
            result += 'id: ' + str(members[i].id) + ', '
            result += 'discriminator: ' + members[i].discriminator
            result += '\n'
        await ctx.channel.send(result)


class Mode(commands.Cog):
    def __init__(self, bot: commands.Bot, mm: ModeManager):
        self.bot = bot
        self.mm = mm

    @commands.command()
    async def get_mode(self, ctx):
        """Get current mode"""
        await ctx.channel.send('mode = {0}'.format(self.mm.get_mode()))

    @commands.command()
    async def set_mode(self, ctx, new_mode):
        """
        Set mode (0 - off; 1 - mode 1; 2 - mode 2)
        """
        if new_mode not in ['0', '1', '2']:
            await ctx.channel.send('Неправильный аргумент')  # 2
            return
        new_mode = int(new_mode)
        await self.mm.set_mode(self.bot, new_mode)
        await ctx.channel.send('mode = {0}'.format(self.mm.get_mode()))  # 3

    @commands.command()
    async def set_voice_channel(self, ctx, number):
        """
        Set voice channel for mode 2
        """

        if not number.isdigit():
            await ctx.channel.send('Неправильный аргумент')
            return

        new_channel = self.mm.voice_channel_for_mode_2

        if number.isdigit():
            number = int(number)
            if 1 <= number <= len(ctx.guild.voice_channels):
                new_guild = ctx.guild
                new_channel = ctx.guild.voice_channels[number - 1]

                if not new_guild.me.permissions_in(new_channel).connect:
                    await ctx.channel.send('Нет доступа к этому каналу')
                    return

            elif number == 0:
                new_channel = None

            else:
                await ctx.channel.send('Неправильное число')
                return

        await self.mm.set_voice_channel(self.bot, new_channel)

        # send response
        if self.mm.voice_channel_for_mode_2 is None:
            await ctx.channel.send('Номер голосового чата сброшен')
        else:
            addition = 'Название: ' + self.mm.voice_channel_for_mode_2.name
            await ctx.channel.send('Номер голосового чата: ' +
                                   str(number) +
                                   '\n' + addition)


class Greet(commands.Cog):
    def __init__(self, bot: commands.Bot, gr: Greeter):
        self.bot = bot
        self.gr = gr

    @commands.command()
    async def play_greet(self, ctx: commands.Context):
        """
        if bot is connected play greeting message
        """
        executable_path = cfg.executable_path
        if connection.is_connected(self.bot):
            voice_client = self.bot.voice_clients[0]
            if os.name == 'nt':
                voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                         source=self.gr.greet_path))
            elif os.name == 'posix':
                voice_client.play(discord.FFmpegPCMAudio(source=self.gr.greet_path))

            while voice_client.is_playing():
                await asyncio.sleep(1)

    @commands.command()
    async def get_greet(self, ctx: commands.Context):
        """
        Get current greeting message
        """
        await ctx.channel.send('greet = {0}'.format(self.gr.get_greet()))

    @commands.command()
    async def set_greet(self, ctx: commands.Context, new_greet: str):
        """
        Set greeting message
        """
        new_greet = ' '.join(new_greet.split('_'))
        self.gr.set_greet(new_greet)
        await ctx.channel.send('greet = {0}'.format(self.gr.get_greet()))

    @commands.command()
    async def set_default_greet(self, ctx: commands.Context):
        """
        Set default greeting message
        """
        self.gr.set_default_greet()
        await ctx.channel.send('greet = {0}'.format(self.gr.get_greet()))

    @commands.command()
    async def set_name(self, ctx: commands.Context,
                       name_and_disc: str,
                       extra_name: str):
        """
        Set special name (extra_name) for some user (name_and_disc)
        """
        extra_name = ' '.join(extra_name.split('_'))
        mes = self.gr.set_name(name_and_disc, extra_name, ctx.guild.members)
        await ctx.channel.send(mes)

    @commands.command()
    async def get_name(self, ctx, name_and_disc):
        """
        Get name (rewrite)
        """
        await ctx.channel.send(self.gr.get_name(name_and_disc, ctx.guild.members))

    @commands.command()
    async def extra_names(self, ctx, arg):
        """
        Include or exclude extra names (0 - off, 1 - on)
        """
        if arg == '0':
            self.gr.extra_names_off()
            await ctx.channel.send('Дополнительные имена теперь не доступны')

        elif arg == '1':
            self.gr.extra_names_on()
            await ctx.channel.send('Дополнительные имена теперь доступны')

        else:
            await ctx.channel.send('Неправильный аргумент')

