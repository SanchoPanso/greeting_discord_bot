import discord
from discord.ext import commands
import asyncio
import csv
import os
import pyttsx3
from config import settings
from my_module import Greeting, ModeManager
from my_module import connecting, disconnecting, is_connected
from my_module import is_right_form_of_name_and_disc

greeting = Greeting()
mode_manager = ModeManager()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=settings['prefix'],
                   intents=intents)


@bot.command()
async def hello(ctx):
    """
    Send "Hello World!"
    """
    await ctx.channel.send('**Hello World!**')


@bot.command()
async def connect(ctx, number):
    global voice_client

    if not number.isdigit():
        await ctx.channel.send('Неправильный аргумент')  # 1
        return

    number = int(number)

    if not (1 <= number <= len(ctx.guild.voice_channels)):
        await ctx.channel.send('Неправильный аргумент')  # 2
        return

    new_channel = ctx.guild.voice_channels[number - 1]

    await connecting(bot, new_channel)


@bot.command()
async def disconnect(ctx):
    await ctx.guild.change_voice_state(channel=None,
                                       self_mute=False,
                                       self_deaf=False)


@bot.command()
async def play_greet(ctx):
    executable_path = "ffmpeg-20200831-4a11a6f-win64-static/bin/ffmpeg.exe"
    if is_connected(bot):
        voice_client = bot.voice_clients[0]
        if os.name == 'nt':
            voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                     source=greeting.greet_path))
        elif os.name == 'posix':
            voice_client.play(discord.FFmpegPCMAudio(source=greeting.greet_path))

        while voice_client.is_playing():
            await asyncio.sleep(1)


@bot.command()
async def voice_members_info(ctx):
    for channel in ctx.guild.voice_channels:
        await ctx.channel.send(channel)
        for member in channel.members:
            await ctx.channel.send(member)


@bot.command()
async def members_info(ctx):
    members = ctx.guild.members
    await ctx.channel.send(members)


@bot.command()
async def members_brief_info(ctx):
    members = ctx.guild.members
    result = ''
    for i in range(len(members)):
        result += 'name: ' + members[i].name + ', '
        result += 'id: ' + str(members[i].id) + ', '
        result += 'discriminator: ' + members[i].discriminator
        result += '\n'
    await ctx.channel.send(result)


@bot.command()
async def get_mode(ctx):
    await ctx.channel.send('mode = {0}'.format(mode_manager.get_mode()))


@bot.command()
async def set_mode(ctx, new_mode):
    if new_mode not in ['0', '1', '2']:
        await ctx.channel.send('Неправильный аргумент')  # 2
        return
    new_mode = int(new_mode)
    await mode_manager.set_mode(bot, new_mode)
    await ctx.channel.send('mode = {0}'.format(mode_manager.get_mode()))  # 3


@bot.command()
async def get_greet(ctx):
    await ctx.channel.send('greet = {0}'.format(greeting.get_greet()))


@bot.command()
async def set_greet(ctx, new_greet):
    new_greet = ' '.join(new_greet.split('_'))
    greeting.set_greet(new_greet)
    await ctx.channel.send('greet = {0}'.format(greeting.get_greet()))


@bot.command()
async def set_default_greet(ctx):
    greeting.set_default_greet()
    await ctx.channel.send('greet = {0}'.format(greeting.get_greet()))


@bot.command()
async def set_voice_channel(ctx, number):
    new_channel = mode_manager.voice_channel_for_mode_2

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

    await mode_manager.set_voice_channel(bot, new_channel)

    if mode_manager.voice_channel_for_mode_2 is None:
        await ctx.channel.send('Номер голосового чата сброшен')
    else:
        addition = 'Название: ' + mode_manager.voice_channel_for_mode_2.name
        await ctx.channel.send('Номер голосового чата: ' +
                               str(number) +
                               '\n' + addition)  # 4


@bot.command()
async def set_name(ctx, name_and_disc, extra_name):
    extra_name = ' '.join(extra_name.split('_'))

    if not is_right_form_of_name_and_disc(name_and_disc):
        await ctx.channel.send('Неправильный формат имени пользователя')
        return

    mes = greeting.set_name(name_and_disc, extra_name, ctx.guild.members)
    await ctx.channel.send(mes)


@bot.command()
async def get_name(ctx, name_and_disc):
    await ctx.channel.send(greeting.get_name(name_and_disc, ctx.guild.members))


@bot.command()
async def extra_names(ctx, arg):
    if arg == '0':
        greeting.extra_off()
        await ctx.channel.send('Дополнительные имена теперь не доступны')

    elif arg == '1':
        greeting.extra_on()
        await ctx.channel.send('Дополнительные имена теперь доступны')

    else:
        await ctx.channel.send('Неправильный аргумент')


@bot.event
async def on_ready():
    print('Ready!')
    print(os.name)


@bot.event
async def on_voice_state_update(member, before, after):
    executable_path = "ffmpeg-20200831-4a11a6f-win64-static/bin/ffmpeg.exe"

    if mode_manager.mode == 1:

        cond1 = before.channel is not after.channel
        cond2 = after.channel is not None
        cond3 = member.id != bot.user.id
        cond4 = after.channel.guild.me.permissions_in(after.channel).connect if cond2 else False

        all_conditions_are_true = cond1 and cond2 and cond3 and cond4

        if all_conditions_are_true:
            # print(member)  # debug
            greeting.prepare_file_for_playing(after, member)

            voice_client = await connecting(bot, after.channel)

            while voice_client.is_playing():
                await asyncio.sleep(1)
            # print('sleep_before_playing')  # debug

            await asyncio.sleep(1)

            if os.name == 'nt':
                voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                         source=greeting.greet_path))
            elif os.name == 'posix':
                voice_client.play(discord.FFmpegPCMAudio(source=greeting.greet_path))

            while voice_client.is_playing():
                await asyncio.sleep(1)
            # print('sleep_after_playing')  # debug

            await disconnecting(bot)

    elif mode_manager.mode == 2:
        if mode_manager.voice_channel_for_mode_2 is not None and member.id != bot.user.id:

            if before.channel != mode_manager.voice_channel_for_mode_2:
                if after.channel == mode_manager.voice_channel_for_mode_2:

                    greeting.prepare_file_for_playing(after, member)

                    voice_client = await connecting(bot, after.channel)

                    while voice_client.is_playing():
                        await asyncio.sleep(1)
                        # print('sleep_before_playing')  # debug
                    await asyncio.sleep(1)

                    if os.name == 'nt':
                        voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                                source=greeting.greet_path))
                    elif os.name == 'posix':
                        voice_client.play(discord.FFmpegPCMAudio(source=greeting.greet_path))

                    while voice_client.is_playing():
                        await asyncio.sleep(1)
                        # print('sleep_after_playing')  # debug

            if before.channel == mode_manager.voice_channel_for_mode_2:
                if after.channel != mode_manager.voice_channel_for_mode_2:
                    if is_connected(bot):
                        voice_client = bot.voice_clients[0]
                        if len(mode_manager.voice_channel_for_mode_2.members) == 1:
                            await voice_client.disconnect()


bot.run(settings['token'])

########################################################################


greet_path = 'greet.mp3'  # имя файла для записи голоса
names_path = 'names.csv'
names_buffer_path = 'names_buffer.csv'
help_path = 'help.csv'
default_greet = 'Приветствую'  # приветствие по умолчанию
greet = default_greet  # переменная приветствия
mode = 1  # режим работы (0, 1, 2)
is_connected = False  # подключен ли бот
voice_channel_for_mode_2 = None  # голосовой канал для режима №2
voice_client = None  # переменная для голосового клиента
extra_names_are_available = False


def try_to_find_extra_name(name, discriminator, members, path1, path2):
    fieldnames = ['id', 'name_and_disc', 'extra_name']
    output = name

    path = path1
    if not os.path.exists(path1):  #### подумать над предупреждением
        if os.path.exists(path2):
            os.rename(path2, path1)
            path = path1
        else:
            return output

    id = -1
    for member in members:
        if discriminator == member.discriminator:
            if name == member.name:
                id = member.id
                break

    if id == -1:
        return output  ###########

    with open(path, "r") as f_obj:
        reader = csv.DictReader(f_obj, delimiter=';')
        for row in reader:
            if str(id) == row[fieldnames[0]]:
                output = row[fieldnames[2]]
                break

    return output


def is_right_form_of_name_and_disc(name_and_disc):
    if len(name_and_disc) <= 4:
        return False

    if len(name_and_disc) > 5:
        if name_and_disc[-5] != '#' or (not name_and_disc[-4:].isdigit()):
            return False

    return True


def file_can_be_made(greet_path, greet, name):
    try:
        mes = greet + ', ' + name
        print(mes)
        engine = pyttsx3.init()
        engine.save_to_file(mes, greet_path)
        engine.runAndWait()
        return True
    except:
        return False


def prepare_file_for_playing(greet_path, after, member):
    global default_greet
    if extra_names_are_available:
        name = try_to_find_extra_name(member.name,
                                      member.discriminator,
                                      after.channel.guild.members,
                                      names_path,
                                      names_buffer_path)
    else:
        name = member.name

    if file_can_be_made(greet_path, greet, name):  # пробуем новое приветствие и новое имя
        return
    elif file_can_be_made(greet_path, greet, member.name):  # пробуем новое притствие и обычное имя
        return
    elif file_can_be_made(greet_path, greet, ''):  # пробуем новое приветствие и без имени
        return
    elif file_can_be_made(greet_path, default_greet, ''):  # если ничего не подошло, выдаем дефолтное
        return
    file_can_be_made(greet_path, 'Hi', '')  # если и это не подошло, выдаем англ вариант
    return


class MyClient(discord.Client):

    async def on_message(self, message):

        global mode
        global greet
        global voice_channel_for_mode_2
        global voice_client
        global extra_names_are_available
        global names_path
        global names_buffer_path
        global help_path

        my_guild = message.guild  # надо удалить          #

        if message.author == self.user:
            return

        lines = message.content.split('\n')
        for line in lines:

            if line.split()[0] == settings['prefix'] + 'hello':  # checked
                await message.channel.send('**Hello World!**')
                continue

            if line.split()[0] == settings['prefix'] + 'connect':  # checked
                if len(line.split()) > 1:
                    number = line.split()[1]
                    if not number.isdigit():
                        await message.channel.send('Аргумент должен быть числом')  # 1
                        continue

                    number = int(number)  # can be float!!!

                    if not (1 <= number <= len(message.guild.voice_channels)):
                        await message.channel.send('Неверное число')  # 2
                        continue

                    new_channel = message.guild.voice_channels[number - 1]

                    if voice_client is not None:
                        if voice_client.is_connected():
                            if voice_client.channel != new_channel:
                                await voice_client.disconnect()
                                voice_client = await new_channel.connect()
                            else:
                                pass
                        else:
                            voice_client = await new_channel.connect()
                    else:
                        voice_client = await message.guild.voice_channels[number - 1].connect()

                    if voice_client.is_connected():
                        await message.channel.send(f'Успешно подключено к каналу {number}')  # 3
                continue

            if line.split()[0] == settings['prefix'] + 'disconnect':  # checked
                await message.guild.change_voice_state(channel=None,
                                                       self_mute=False,
                                                       self_deaf=False)

                await asyncio.sleep(1)
                if voice_client is None:
                    await message.channel.send('Успешно отключено')
                if voice_client is not None:
                    if not voice_client.is_connected():
                        await message.channel.send('Успешно отключено')

                voice_client = None
                continue

            if line.split()[0] == settings['prefix'] + 'voice_members_info':  # checked
                for channel in my_guild.voice_channels:
                    await message.channel.send(channel)
                    for member in channel.members:
                        await message.channel.send(member)
                continue

            if line.split()[0] == settings['prefix'] + 'members_info':  # информация об участниках канала
                members = message.guild.members  # checked
                await message.channel.send(members)
                continue

            if line.split()[0] == settings['prefix'] + 'members_brief_info':  # информация об участниках канала (кратко)
                members = message.guild.members  # checked
                result = ''
                for i in range(len(members)):
                    result += 'name: ' + members[i].name + ', '
                    result += 'id: ' + str(members[i].id) + ', '
                    result += 'discriminator: ' + members[i].discriminator
                    result += '\n'
                await message.channel.send(result)
                continue

            if line.split()[0] == settings['prefix'] + 'mode':  # режим работы
                if len(line.split()) == 1:
                    await message.channel.send('mode = {0}'.format(mode))  # 1

                elif len(line.split()) > 1:
                    mode_new = line.split()[1]
                    if mode_new not in ['0', '1', '2']:
                        await message.channel.send('Неправильный аргумент')  # 2
                        continue

                    mode_new = int(mode_new)

                    if voice_client is not None and mode != mode_new:
                        while voice_client.is_playing():  #####
                            await asyncio.sleep(1)
                        if voice_client.is_connected():
                            await voice_client.disconnect()

                    if mode_new == 2:
                        if voice_channel_for_mode_2 is not None:
                            if len(voice_channel_for_mode_2.members) > 0:
                                voice_client = await voice_channel_for_mode_2.connect()

                    mode = mode_new
                    await message.channel.send('mode = {0}'.format(mode))  # 3
                continue

            if line.split()[0] == settings['prefix'] + 'set_greet':  # установка приветствия checked
                if len(line.split()) > 1:
                    greet = ' '.join(line.split(' ')[1:])
                    await message.channel.send('greet = {0}'.format(greet))
                continue

            if line.split()[0] == settings['prefix'] + 'get_greet':  # получение приветствия checked
                await message.channel.send('greet = {0}'.format(greet))
                continue

            if line.split()[0] == settings['prefix'] + 'set_default_greet':  # установка приветствия по умолчанию
                greet = default_greet  # checked
                await message.channel.send('greet = {0}'.format(greet))
                continue

            if line.split()[0] == settings['prefix'] + 'set_voice_channel':  #
                if len(line.split()) > 1:

                    voice_channel_for_mode_2_new = voice_channel_for_mode_2

                    if line.split()[1].isdigit():
                        number = int(line.split()[1])  # can be float
                        if 1 <= number <= len(message.guild.voice_channels):

                            new_guild = message.guild
                            new_channel = message.guild.voice_channels[number - 1]

                            if new_guild.me.permissions_in(new_channel).connect:
                                voice_channel_for_mode_2_new = new_channel
                            else:
                                await message.channel.send('Нет доступа к этому каналу')
                                continue
                        else:
                            await message.channel.send('Неправильное число')  # 1
                            continue

                    elif line.split()[1].lower() == 'none':
                        voice_channel_for_mode_2_new = None
                    else:
                        await message.channel.send('Неправильный аргумент')  # 2
                        continue

                    if mode == 2:
                        if voice_channel_for_mode_2 != voice_channel_for_mode_2_new:
                            if voice_channel_for_mode_2 is not None:
                                if voice_client is not None:
                                    if voice_client.is_connected():
                                        await voice_client.disconnect()
                                        voice_client = None

                            if voice_channel_for_mode_2_new is not None:
                                if len(voice_channel_for_mode_2_new.members) > 0:
                                    voice_client = await voice_channel_for_mode_2_new.connect()

                    voice_channel_for_mode_2 = voice_channel_for_mode_2_new

                    if voice_channel_for_mode_2 is None:
                        await message.channel.send('Номер голосового чата сброшен')
                    else:
                        addition = 'Название: ' + voice_channel_for_mode_2.name
                        await message.channel.send('Номер голосового чата: ' +
                                                   str(number) +
                                                   '\n' + addition)  # 4
                continue

            if line.split()[0] == settings['prefix'] + 'set_name':  #

                if len(line.split()) > 2:

                    name_and_disc = line.split()[1]
                    extra_name = ' '.join(line.split('_'))

                    if not is_right_form_of_name_and_disc(name_and_disc):
                        await message.channel.send('Неправильный формат имени пользователя')
                        return

                    id = -1
                    for member in message.guild.members:
                        if member.discriminator == name_and_disc[-4:]:
                            if member.name == name_and_disc[:-5]:
                                id = member.id

                    if id == -1:
                        await message.channel.send('Пользователя нет в списке участников сервера')
                        return

                    data = []
                    fieldnames = ['id', 'name_and_disc', 'extra_name']

                    if not os.path.exists(names_path):  #####
                        if os.path.exists(names_buffer_path):
                            os.rename(names_buffer_path, names_path)
                        else:
                            await message.channel.send('Файл с именами не найден')
                            return

                    with open(names_path, "r") as f_obj:
                        reader = csv.DictReader(f_obj, delimiter=';')
                        for row in reader:
                            data.append({fieldnames[0]: row[fieldnames[0]],
                                         fieldnames[1]: row[fieldnames[1]],
                                         fieldnames[2]: row[fieldnames[2]]})

                    n = -1
                    for i in range(len(data)):
                        if data[i][fieldnames[0]] == str(id):
                            n = i
                            break

                    if n == -1:
                        data.append({fieldnames[0]: id,
                                     fieldnames[1]: name_and_disc,
                                     fieldnames[2]: extra_name})
                    else:
                        data[n] = {fieldnames[0]: id,
                                   fieldnames[1]: name_and_disc,
                                   fieldnames[2]: extra_name}

                    with open(names_buffer_path, "w", newline='') as out_file:
                        writer = csv.DictWriter(out_file, delimiter=';', fieldnames=fieldnames)
                        writer.writeheader()
                        for row in data:
                            writer.writerow(row)

                    os.remove(names_path)  #
                    os.rename(names_buffer_path, names_path)  #
                    await message.channel.send('Успешно')
                continue

            if line.split()[0] == settings['prefix'] + 'get_name':
                if len(line.split()) > 1:
                    name_and_disc = line.split()[1]
                    if is_right_form_of_name_and_disc(name_and_disc):
                        await message.channel.send(try_to_find_extra_name(name_and_disc[:-5],
                                                                          name_and_disc[-4:],
                                                                          message.guild.members,
                                                                          names_path,
                                                                          names_buffer_path))
                    else:
                        await message.channel.send('Неправильный формат имени пользователя')
                continue

            if line.split()[0] == settings['prefix'] + 'extra_names':
                if len(line.split()) > 1:
                    if line.split()[1] == '0':
                        extra_names_are_available = False
                        await message.channel.send('Дополнительные именя теперь не доступны')
                    elif line.split()[1] == '1':
                        extra_names_are_available = True
                        await message.channel.send('Дополнительные именя теперь доступны')
                    else:
                        await message.channel.send('Неправильный аргумент')
                continue

            if line.split()[0] == settings['prefix'] + 'help':  # проверено
                output = ''
                if len(line.split()) == 1:
                    output += 'Для получения помощи воспользуйтесь следующими командами:\n'
                    output += '**{0}help list** - '.format(settings['prefix'])
                    output += 'вывод списка команд;\n'
                    output += '**{0}help** [*command*] - '.format(settings['prefix'])
                    output += 'вывод описания команды, '
                    output += 'где [*command*] - название команды без префикса и аргументов'
                    output += '(в настоящее время префикс **{0}**);\n'.format(settings['prefix'])
                    output += '**{0}help all** - '.format(settings['prefix'])
                    output += 'вывод описания всех команд.\n'
                    await message.channel.send(output)

                elif len(line.split()) > 1:
                    with open(help_path, "r") as f_obj:
                        reader = csv.DictReader(f_obj, delimiter=';')
                        command = line.split()[1]

                        if command == 'list':
                            for row in reader:
                                output += row['Command'] + '\n'

                        elif command == 'all':
                            for row in reader:
                                output = ''
                                output += row['Command'] + '\n'
                                output += '\n'.join(row['Description'].split('\\' + 'n')) + '\n'
                                output += '\n'
                                await message.channel.send(output)

                        else:
                            for row in reader:
                                if command == row['Command'][5:5 + len(command)]:
                                    output += row['Command'] + '\n'
                                    output += '\n'.join(row['Description'].split('\\' + 'n')) + '\n'
                                    output += '\n'

                        if output == '':
                            await message.channel.send('Такой команды нет')
                        else:
                            output = settings['prefix'].join(output.split('$'))
                            await message.channel.send(output)
                continue

    async def on_voice_state_update(self, member, before, after):

        executable_path = "ffmpeg-20200831-4a11a6f-win64-static/bin/ffmpeg.exe"
        global voice_client
        global extra_names_are_available
        global names_path
        global names_buffer_path
        global greet_path

        if mode == 1:

            if before.channel is None and after.channel is not None and member.id != 0:
                if after.channel.guild.me.permissions_in(after.channel).connect:

                    print(member)  # debug

                    prepare_file_for_playing(greet_path, after, member)

                    # voice_client = discord.VoiceClient()#############ЗАКОММЕНТИТЬ

                    if voice_client is None:
                        voice_client = await after.channel.connect()
                    elif not voice_client.is_connected():
                        voice_client = await after.channel.connect()
                    elif voice_client.channel != after:
                        await voice_client.disconnect()
                        voice_client = await after.channel.connect()

                    # if not is_connected:
                    # voice_client_local = await after.channel.connect()
                    # is_connected = True
                    # voice_client = voice_client_local
                    # else:
                    # voice_client_local = voice_client

                    while voice_client.is_playing():
                        await asyncio.sleep(1)
                        print('sleep_before_playing')  # debug

                    voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                                                             source=greet_path))
                    # voice_client.play(discord.FFmpegPCMAudio(greet_path))
                    # except Exception as e:
                    # await self.guilds[0].text_channels[0].send(e)
                    # await self.guilds[0].text_channels[0].send(e)
                    # await asyncio.sleep(1)

                    while voice_client.is_playing():
                        await asyncio.sleep(1)
                        print('sleep_after_playing')  # debug

                    if voice_client.is_connected():
                        await voice_client.disconnect()

        elif mode == 2:

            if voice_channel_for_mode_2 is not None and member.id != 0:

                if before.channel != voice_channel_for_mode_2:
                    if after.channel == voice_channel_for_mode_2:

                        prepare_file_for_playing(greet_path, after, member)

                        if voice_client is None:
                            voice_client = await after.channel.connect()
                        elif not voice_client.is_connected():
                            voice_client = await after.channel.connect()
                        elif voice_client.channel != after:
                            await voice_client.disconnect()
                            voice_client = await after.channel.connect()

                        # if not is_connected:
                        # voice_client_local = await after.channel.connect()
                        # is_connected = True
                        # voice_client = voice_client_local
                        # else:
                        # voice_client_local = voice_client

                        while voice_client.is_playing():
                            await asyncio.sleep(1)
                            print('sleep_before_playing')  # debug

                        # voice_client.play(discord.FFmpegPCMAudio(executable=executable_path,
                        # source=greet_path))
                        while voice_client.is_playing():
                            await asyncio.sleep(1)
                            print('sleep_after_playing')  # debug

                if before.channel == voice_channel_for_mode_2:
                    if after.channel != voice_channel_for_mode_2:
                        if voice_client.is_connected():
                            if len(voice_channel_for_mode_2.members) == 1:
                                await voice_client.disconnect()
                                voice_client = None

    async def on_guild_channel_delete(self, channel):
        global voice_client
        if voice_client is not None:
            if voice_client.is_connected():
                if voice_client.channel == channel:
                    try:  # maybe not important
                        await voice_client.diconnect()
                    except:
                        pass
                    voice_client = None

    async def on_ready(self):

        print('ready')  # debug


client = MyClient(intents=intents)
# client.run(settings['token'])




async def help_(ctx, *arg):
    output = ''
    if len(arg) == 0:
        output += 'Для получения помощи воспользуйтесь следующими командами:\n'
        output += '**{0}help list** - '.format(settings['prefix'])
        output += 'вывод списка команд;\n'
        output += '**{0}help** [*command*] - '.format(settings['prefix'])
        output += 'вывод описания команды, '
        output += 'где [*command*] - название команды без префикса и аргументов'
        output += '(в настоящее время префикс **{0}**);\n'.format(settings['prefix'])
        output += '**{0}help all** - '.format(settings['prefix'])
        output += 'вывод описания всех команд.\n'
        await ctx.channel.send(output)

    elif len(arg) > 1:
        with open(help_path, "r") as f_obj:
            reader = csv.DictReader(f_obj, delimiter=';')
            command = arg[1]

            if command == 'list':
                for row in reader:
                    output += row['Command'] + '\n'

            elif command == 'all':
                for row in reader:
                    output = ''
                    output += row['Command'] + '\n'
                    output += '\n'.join(row['Description'].split('\\' + 'n')) + '\n'
                    output += '\n'
                    await ctx.channel.send(output)

            else:
                for row in reader:
                    if command == row['Command'][5: 5+len(command)]:
                        output += row['Command'] + '\n'
                        output += '\n'.join(row['Description'].split('\\' + 'n')) + '\n'
                        output += '\n'

            if output == '':
                await ctx.channel.send('Такой команды нет')
            else:
                output = settings['prefix'].join(output.split('$'))
                await ctx.channel.send(output)