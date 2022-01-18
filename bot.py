import discord
from discord.ext import commands
import asyncio
import os
from os import getenv
from sys import exit

from config import settings, paths
from connection_module import connecting, disconnecting, is_connected
from mode_manager_module import ModeManager
from greeting_module import Greeter
import cogs

# greeting = Greeting()
# mode_manager = ModeManager()

intents = discord.Intents.default()
intents.members = True

# bot = commands.Bot(command_prefix=settings['prefix'],
#                    intents=intents)


class GreetingBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=settings['prefix'], intents=intents)
        self.greeting = Greeter()
        self.mode_manager = ModeManager()

        self.add_cog(cogs.Base(self))
        self.add_cog(cogs.Mode(self, self.mode_manager))
        self.add_cog(cogs.Greet(self, self.greeting))

    async def on_ready(self):
        print('Ready!')
        print(f"OS is {os.name}")

    async def on_voice_state_update(self, member, before, after):
        executable_path = paths['executable_path']

        if self.mode_manager.mode == 1:

            cond1 = before.channel is not after.channel
            cond2 = after.channel is not None
            cond3 = member.id != self.user.id
            cond4 = after.channel.guild.me.permissions_in(after.channel).connect if cond2 else False

            all_conditions_are_true = cond1 and cond2 and cond3 and cond4

            if all_conditions_are_true:
                # print(member)  # debug
                self.greeting.prepare_file_for_playing(after, member)

                voice_client = await connecting(self, after.channel)

                while voice_client.is_playing():
                    await asyncio.sleep(1)
                # print('sleep_before_playing')  # debug

                # await asyncio.sleep(1)

                if os.name == 'nt':
                    voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                             source=self.greeting.greet_path))
                elif os.name == 'posix':
                    voice_client.play(discord.FFmpegPCMAudio(source=self.greeting.greet_path))

                while voice_client.is_playing():
                    await asyncio.sleep(1)
                # print('sleep_after_playing')  # debug

                await disconnecting(self)

        elif self.mode_manager.mode == 2:
            if self.mode_manager.voice_channel_for_mode_2 is not None and member.id != self.user.id:

                if before.channel != self.mode_manager.voice_channel_for_mode_2:
                    if after.channel == self.mode_manager.voice_channel_for_mode_2:

                        self.greeting.prepare_file_for_playing(after, member)

                        voice_client = await connecting(self, after.channel)

                        while voice_client.is_playing():
                            await asyncio.sleep(1)
                            # print('sleep_before_playing')  # debug
                        await asyncio.sleep(1)

                        if os.name == 'nt':
                            voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                                     source=self.greeting.greet_path))
                        elif os.name == 'posix':
                            voice_client.play(discord.FFmpegPCMAudio(source=self.greeting.greet_path))

                        while voice_client.is_playing():
                            await asyncio.sleep(1)
                            # print('sleep_after_playing')  # debug

                if before.channel == self.mode_manager.voice_channel_for_mode_2:
                    if after.channel != self.mode_manager.voice_channel_for_mode_2:
                        if is_connected(self):
                            voice_client = self.voice_clients[0]
                            if len(self.mode_manager.voice_channel_for_mode_2.members) == 1:
                                await voice_client.disconnect()

    def init_commands(self):

        @self.command()
        async def hello(ctx):
            """
            Send "Hello World!"
            """
            await ctx.channel.send('**Hello World!**')

        @self.command()
        async def connect(ctx, number):
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

            await connecting(self, new_channel)

        @self.command()
        async def disconnect(ctx):
            """
            disconnect from any voice channel
            :param ctx:
            :return:
            """
            await ctx.guild.change_voice_state(channel=None,
                                               self_mute=False,
                                               self_deaf=False)

        @self.command()
        async def play_greet(ctx):
            """
            if bot is connected play greeting message
            :param ctx:
            :return:
            """
            executable_path = paths['executable_path']
            if is_connected(self):
                voice_client = self.voice_clients[0]
                if os.name == 'nt':
                    voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                             source=self.greeting.greet_path))
                elif os.name == 'posix':
                    voice_client.play(discord.FFmpegPCMAudio(source=self.greeting.greet_path))

                while voice_client.is_playing():
                    await asyncio.sleep(1)

        @self.command()
        async def voice_members_info(ctx):
            for channel in ctx.guild.voice_channels:
                await ctx.channel.send(channel)
                for member in channel.members:
                    await ctx.channel.send(member)

        @self.command()
        async def members_info(ctx):
            members = ctx.guild.members
            await ctx.channel.send(members)

        @self.command()
        async def members_brief_info(ctx):
            members = ctx.guild.members
            result = ''
            for i in range(len(members)):
                result += 'name: ' + members[i].name + ', '
                result += 'id: ' + str(members[i].id) + ', '
                result += 'discriminator: ' + members[i].discriminator
                result += '\n'
            await ctx.channel.send(result)

        @self.command()
        async def get_mode(ctx):
            await ctx.channel.send('mode = {0}'.format(self.mode_manager.get_mode()))

        @self.command()
        async def set_mode(ctx, new_mode):
            if new_mode not in ['0', '1', '2']:
                await ctx.channel.send('Неправильный аргумент')  # 2
                return
            new_mode = int(new_mode)
            await self.mode_manager.set_mode(self, new_mode)
            await ctx.channel.send('mode = {0}'.format(self.mode_manager.get_mode()))  # 3

        @self.command()
        async def get_greet(ctx):
            await ctx.channel.send('greet = {0}'.format(self.greeting.get_greet()))

        @self.command()
        async def set_greet(ctx, new_greet):
            new_greet = ' '.join(new_greet.split('_'))
            self.greeting.set_greet(new_greet)
            await ctx.channel.send('greet = {0}'.format(self.greeting.get_greet()))

        @self.command()
        async def set_default_greet(ctx):
            self.greeting.set_default_greet()
            await ctx.channel.send('greet = {0}'.format(self.greeting.get_greet()))

        @self.command()
        async def set_voice_channel(ctx, number):
            """

            :param ctx:
            :param number:
            :return:
            """
            new_channel = self.mode_manager.voice_channel_for_mode_2

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

            await self.mode_manager.set_voice_channel(self, new_channel)

            if self.mode_manager.voice_channel_for_mode_2 is None:
                await ctx.channel.send('Номер голосового чата сброшен')
            else:
                addition = 'Название: ' + self.mode_manager.voice_channel_for_mode_2.name
                await ctx.channel.send('Номер голосового чата: ' +
                                       str(number) +
                                       '\n' + addition)  # 4

        @self.command()
        async def set_name(ctx, name_and_disc, extra_name):
            extra_name = ' '.join(extra_name.split('_'))
            mes = self.greeting.set_name(name_and_disc, extra_name, ctx.guild.members)
            await ctx.channel.send(mes)

        @self.command()
        async def get_name(ctx, name_and_disc):
            await ctx.channel.send(self.greeting.get_name(name_and_disc, ctx.guild.members))

        @self.command()
        async def extra_names(ctx, arg):
            if arg == '0':
                self.greeting.extra_names_off()
                await ctx.channel.send('Дополнительные имена теперь не доступны')

            elif arg == '1':
                self.greeting.extra_names_on()
                await ctx.channel.send('Дополнительные имена теперь доступны')

            else:
                await ctx.channel.send('Неправильный аргумент')



if __name__ == '__main__':
    pass
    # bot_token = getenv("BOT_TOKEN")
    # if not bot_token:
    #     exit("Error: no token provided")
    #
    # bot.run(bot_token)
