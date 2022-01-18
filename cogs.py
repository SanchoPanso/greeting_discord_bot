import discord
from discord.ext import commands
import asyncio
import os

from discord.ext import commands
from connection_module import connecting, disconnecting, is_connected
from mode_manager_module import ModeManager
from greeting_module import Greeter
from config import settings, paths


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
        :param ctx: context
        :param number: the number of the voice channel to which you want to connect (numbering begins with one(!?))
        :return: nothing
        """

        if not number.isdigit():
            await ctx.channel.send('Неправильный аргумент')  # 1
            return

        number = int(number)

        if not (1 <= number <= len(ctx.guild.voice_channels)):
            await ctx.channel.send('Неправильный аргумент')  # 2
            return

        new_channel = ctx.guild.voice_channels[number - 1]
        await connecting(self.bot, new_channel)

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        """
        disconnect from any voice channel
        :param ctx:
        :return:
        """
        await ctx.guild.change_voice_state(channel=None,
                                           self_mute=False,
                                           self_deaf=False)

    @commands.command()
    async def voice_members_info(self, ctx: commands.Context):
        for channel in ctx.guild.voice_channels:
            await ctx.channel.send(channel)
            for member in channel.members:
                await ctx.channel.send(member)

    @commands.command()
    async def members_info(self, ctx: commands.Context):
        members = ctx.guild.members
        await ctx.channel.send(members)

    @commands.command()
    async def members_brief_info(self, ctx: commands.Context):
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
        await ctx.channel.send('mode = {0}'.format(self.mm.get_mode()))

    @commands.command()
    async def set_mode(self, ctx, new_mode):
        if new_mode not in ['0', '1', '2']:
            await ctx.channel.send('Неправильный аргумент')  # 2
            return
        new_mode = int(new_mode)
        await self.mm.set_mode(self, new_mode)
        await ctx.channel.send('mode = {0}'.format(self.mm.get_mode()))  # 3

    @commands.command()
    async def set_voice_channel(self, ctx, number):
        """

        :param ctx:
        :param number:
        :return:
        """
        new_channel = self.mm.voice_channel_for_mode_2

        if number.isdigit():
            number = int(number)
            if 1 <= number <= len(ctx.guild.voice_channels):
                new_guild = ctx.guild
                new_channel = ctx.guild.voice_channels[number - 1]

                if not new_guild.me.permissions_in(new_channel).connect:
                    await ctx.channel.send('Нет доступа к этому каналу')
                    return
            else:
                await ctx.channel.send('Неправильное число')  # 1
                return

        elif number.lower() == 'none':
            new_channel = None
        else:
            await ctx.channel.send('Неправильный аргумент')  # 2
            return

        await self.mm.set_voice_channel(self, new_channel)

        if self.mm.voice_channel_for_mode_2 is None:
            await ctx.channel.send('Номер голосового чата сброшен')
        else:
            addition = 'Название: ' + self.mm.voice_channel_for_mode_2.name
            await ctx.channel.send('Номер голосового чата: ' +
                                   str(number) +
                                   '\n' + addition)  # 4


class Greet(commands.Cog):
    def __init__(self, bot: commands.Bot, gr: Greeter):
        self.bot = bot
        self.gr = gr

    @commands.command()
    async def play_greet(self, ctx: commands.Context):
        """
        if bot is connected play greeting message
        :param ctx:
        :return:
        """
        executable_path = paths['executable_path']
        if is_connected(self.bot):
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
        await ctx.channel.send('greet = {0}'.format(self.gr.get_greet()))

    @commands.command()
    async def set_greet(self, ctx: commands.Context, new_greet: str):
        new_greet = ' '.join(new_greet.split('_'))
        self.gr.set_greet(new_greet)
        await ctx.channel.send('greet = {0}'.format(self.gr.get_greet()))

    @commands.command()
    async def set_default_greet(self, ctx: commands.Context):
        self.gr.set_default_greet()
        await ctx.channel.send('greet = {0}'.format(self.gr.get_greet()))

    @commands.command()
    async def set_name(self, ctx, name_and_disc, extra_name):
        extra_name = ' '.join(extra_name.split('_'))
        mes = self.gr.set_name(name_and_disc, extra_name, ctx.guild.members)
        await ctx.channel.send(mes)

    @commands.command()
    async def get_name(self, ctx, name_and_disc):
        await ctx.channel.send(self.gr.get_name(name_and_disc, ctx.guild.members))

    @commands.command()
    async def extra_names(self, ctx, arg):
        if arg == '0':
            self.gr.extra_names_off()
            await ctx.channel.send('Дополнительные имена теперь не доступны')

        elif arg == '1':
            self.gr.extra_names_on()
            await ctx.channel.send('Дополнительные имена теперь доступны')

        else:
            await ctx.channel.send('Неправильный аргумент')


class BotCog(commands.Cog):
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
        :param ctx: context
        :param number: the number of the voice channel to which you want to connect (numbering begins with one(!?))
        :return: nothing
        """

        if not number.isdigit():
            await ctx.channel.send('Неправильный аргумент')  # 1
            return

        number = int(number)

        if not (1 <= number <= len(ctx.guild.voice_channels)):
            await ctx.channel.send('Неправильный аргумент')  # 2
            return

        new_channel = ctx.guild.voice_channels[number - 1]
        await connecting(self.bot, new_channel)

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        """
        disconnect from any voice channel
        :param ctx:
        :return:
        """
        await ctx.guild.change_voice_state(channel=None,
                                           self_mute=False,
                                           self_deaf=False)

    @commands.command()
    async def play_greet(self, ctx: commands.Context):
        """
        if bot is connected play greeting message
        :param ctx:
        :return:
        """
        executable_path = paths['executable_path']
        if is_connected(self.bot):
            voice_client = self.bot.voice_clients[0]
            if os.name == 'nt':
                voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                         source=self.bot.greeting.greet_path))
            elif os.name == 'posix':
                voice_client.play(discord.FFmpegPCMAudio(source=self.bot.greeting.greet_path))

            while voice_client.is_playing():
                await asyncio.sleep(1)

    @commands.command()
    async def voice_members_info(self, ctx: commands.Context):
        for channel in ctx.guild.voice_channels:
            await ctx.channel.send(channel)
            for member in channel.members:
                await ctx.channel.send(member)

    @commands.command()
    async def members_info(self, ctx: commands.Context):
        members = ctx.guild.members
        await ctx.channel.send(members)

    @commands.command()
    async def members_brief_info(self, ctx: commands.Context):
        members = ctx.guild.members
        result = ''
        for i in range(len(members)):
            result += 'name: ' + members[i].name + ', '
            result += 'id: ' + str(members[i].id) + ', '
            result += 'discriminator: ' + members[i].discriminator
            result += '\n'
        await ctx.channel.send(result)

    @commands.command()
    async def get_mode(self, ctx):
        await ctx.channel.send('mode = {0}'.format(self.bot.mode_manager.get_mode()))

    @commands.command()
    async def set_mode(self, ctx, new_mode):
        if new_mode not in ['0', '1', '2']:
            await ctx.channel.send('Неправильный аргумент')  # 2
            return
        new_mode = int(new_mode)
        await self.bot.mode_manager.set_mode(self, new_mode)
        await ctx.channel.send('mode = {0}'.format(self.bot.mode_manager.get_mode()))  # 3
    #
    # @self.command()
    # async def get_greet(ctx):
    #     await ctx.channel.send('greet = {0}'.format(self.greeting.get_greet()))
    #
    # @self.command()
    # async def set_greet(ctx, new_greet):
    #     new_greet = ' '.join(new_greet.split('_'))
    #     self.greeting.set_greet(new_greet)
    #     await ctx.channel.send('greet = {0}'.format(self.greeting.get_greet()))
    #
    # @self.command()
    # async def set_default_greet(ctx):
    #     self.greeting.set_default_greet()
    #     await ctx.channel.send('greet = {0}'.format(self.greeting.get_greet()))
    #
    # @self.command()
    # async def set_voice_channel(ctx, number):
    #     """
    #
    #     :param ctx:
    #     :param number:
    #     :return:
    #     """
    #     new_channel = self.mode_manager.voice_channel_for_mode_2
    #
    #     if number.isdigit():
    #         number = int(number)
    #         if 1 <= number <= len(ctx.guild.voice_channels):
    #             new_guild = ctx.guild
    #             new_channel = ctx.guild.voice_channels[number - 1]
    #
    #             if not new_guild.me.permissions_in(new_channel).connect:
    #                 await ctx.channel.send('Нет доступа к этому каналу')
    #                 return
    #         else:
    #             await ctx.channel.send('Неправильное число')  # 1
    #             return
    #
    #     elif number.lower() == 'none':
    #         new_channel = None
    #     else:
    #         await ctx.channel.send('Неправильный аргумент')  # 2
    #         return
    #
    #     await self.mode_manager.set_voice_channel(self, new_channel)
    #
    #     if self.mode_manager.voice_channel_for_mode_2 is None:
    #         await ctx.channel.send('Номер голосового чата сброшен')
    #     else:
    #         addition = 'Название: ' + self.mode_manager.voice_channel_for_mode_2.name
    #         await ctx.channel.send('Номер голосового чата: ' +
    #                                str(number) +
    #                                '\n' + addition)  # 4
    #
    # @self.command()
    # async def set_name(ctx, name_and_disc, extra_name):
    #     extra_name = ' '.join(extra_name.split('_'))
    #     mes = self.greeting.set_name(name_and_disc, extra_name, ctx.guild.members)
    #     await ctx.channel.send(mes)
    #
    # @self.command()
    # async def get_name(ctx, name_and_disc):
    #     await ctx.channel.send(self.greeting.get_name(name_and_disc, ctx.guild.members))
    #
    # @self.command()
    # async def extra_names(ctx, arg):
    #     if arg == '0':
    #         self.greeting.extra_off()
    #         await ctx.channel.send('Дополнительные имена теперь не доступны')
    #
    #     elif arg == '1':
    #         self.greeting.extra_on()
    #         await ctx.channel.send('Дополнительные имена теперь доступны')
    #
    #     else:
    #         await ctx.channel.send('Неправильный аргумент')
