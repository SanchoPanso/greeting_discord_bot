from bot import bot
from my_module import connecting, disconnecting, is_connected
from my_module import is_right_form_of_name_and_disc


@bot.command()
async def hello(ctx):
    """
    Send "Hello World!"
    """
    await ctx.channel.send('**Hello World!**')


@bot.command()
async def connect(ctx, number):
    """
    Connect to the voice channel, which is placed in the guild where this command is recalled
    and which has required number
    :param ctx: context
    :param number: the number of the voice channel to which you want to connect (numbering begins with one(!?))
    :return: nothing
    """
    global voice_client     # may be it needs to be removed

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
    """
    disconnect from any voice channel
    :param ctx:
    :return:
    """
    await ctx.guild.change_voice_state(channel=None,
                                       self_mute=False,
                                       self_deaf=False)


@bot.command()
async def play_greet(ctx):
    """
    if bot is connected play greeting message
    :param ctx:
    :return:
    """
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
    """

    :param ctx:
    :param number:
    :return:
    """
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
