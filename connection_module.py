import discord
import pyttsx3
import os
import csv
from config import settings, paths
import asyncio


def is_connected(client):
    if not client.voice_clients:
        return False

    else:
        if client.voice_clients[0].is_connected():
            return True
        else:
            return False


async def connecting(client, given_channel):
    if is_connected(client):
        voice_client = client.voice_clients[0]

        while voice_client.is_playing():
            await asyncio.sleep(1)

        if voice_client.channel != given_channel:
            await voice_client.disconnect()
            voice_client = await given_channel.connect()
    else:
        voice_client = await given_channel.connect()

    return voice_client


async def disconnecting(client):
    if is_connected(client):
        voice_client = client.voice_clients[0]
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()


def is_right_form_of_name_and_disc(name_and_disc):
    if len(name_and_disc) <= 4:
        return False

    if len(name_and_disc) > 5:
        if name_and_disc[-5] != '#' or (not name_and_disc[-4:].isdigit()):
            return False

    return True


class Greeting:

    def __init__(self):
        self.greet_path = paths['greet_path']
        self.names_path = paths['names_path']
        self.names_buffer_path = paths['names_buffer_path']

        self.default_greet = settings['default_greet']
        self.greet = self.default_greet
        self.extra_names_are_available = False

    def get_greet(self):
        return self.greet

    def set_greet(self, new_greet):
        self.greet = new_greet

    def set_default_greet(self):
        self.greet = self.default_greet

    def extra_on(self):
        self.extra_names_are_available = True

    def extra_off(self):
        self.extra_names_are_available = False

    def file_can_be_made(self, greet, name):
        try:
            mes = greet + ', ' + name
            print(mes)
            engine = pyttsx3.init()
            engine.save_to_file(mes, self.greet_path)
            engine.runAndWait()
            return True
        except Exception as e:
            print(e)
            return False

    def try_to_find_extra_name(self, name, discriminator, members):
        fieldnames = ['id', 'name_and_disc', 'extra_name']
        output = name

        path = self.names_path
        if not os.path.exists(self.names_path):
            if os.path.exists(self.names_buffer_path):
                os.rename(self.names_buffer_path, self.names_path)
                path = self.names_path
            else:
                return output

        id = -1
        for member in members:
            if discriminator == member.discriminator:
                if name == member.name:
                    id = member.id
                    break

        if id == -1:
            return output

        with open(path, "r") as f_obj:
            reader = csv.DictReader(f_obj, delimiter=';')
            for row in reader:
                if str(id) == row[fieldnames[0]]:
                    output = row[fieldnames[2]]
                    break

        return output

    def prepare_file_for_playing(self, after, member):
        if self.extra_names_are_available:
            name = self.try_to_find_extra_name(member.name,
                                               member.discriminator,
                                               after.channel.guild.members)
        else:
            name = member.name
        # пробуем новое приветствие и новое имя
        if self.file_can_be_made(self.greet, name):
            return
        # пробуем новое притствие и обычное имя
        elif self.file_can_be_made(self.greet, member.name):
            return
        # пробуем новое приветствие и без имени
        elif self.file_can_be_made(self.greet, ''):
            return
        # если ничего не подошло, выдаем дефолтное
        elif self.file_can_be_made(self.default_greet, ''):
            return
        # если и это не подошло, выдаем англ вариант
        self.file_can_be_made('Hi', '')

    def set_name(self, name_and_disc, extra_name, members):
        id = -1
        for member in members:
            if member.discriminator == name_and_disc[-4:]:
                if member.name == name_and_disc[:-5]:
                    id = member.id

        if id == -1:
            return 'Пользователя нет в списке участников сервера'

        data = []
        fieldnames = ['id', 'name_and_disc', 'extra_name']

        if not os.path.exists(self.names_path):
            if os.path.exists(self.names_buffer_path):
                os.rename(self.names_buffer_path, self.names_path)
            else:
                return 'Файл с именами не найден'

        with open(self.names_path, "r") as f_obj:
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

        with open(self.names_buffer_path, "w", newline='') as out_file:
            writer = csv.DictWriter(out_file, delimiter=';', fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        os.remove(self.names_path)
        os.rename(self.names_buffer_path, self.names_path)
        return 'Успешно'

    def get_name(self, name_and_disc, members):
        if is_right_form_of_name_and_disc(name_and_disc):
            return self.try_to_find_extra_name(name_and_disc[:-5],
                                               name_and_disc[-4:],
                                               members)
        else:
            return 'Неправильный формат имени пользователя'


class ModeManager:
    def __init__(self):
        self.mode = 1
        self.voice_channel_for_mode_2 = None

    def get_mode(self):
        return self.mode

    async def set_mode(self, client, new_mode):
        if is_connected(client) and self.mode != new_mode:
            voice_client = client.voice_clients[0]
            while voice_client.is_playing():
                await asyncio.sleep(1)
            await disconnecting(client)

        if new_mode == 2:
            if self.voice_channel_for_mode_2 is not None:
                if len(self.voice_channel_for_mode_2.members) > 0:
                    await connecting(client, self.voice_channel_for_mode_2)

        self.mode = new_mode

    async def set_voice_channel(self, client, new_channel):
        if self.mode == 2:
            if self.voice_channel_for_mode_2 != new_channel:
                if self.voice_channel_for_mode_2 is not None:
                    await disconnecting(client)

                if new_channel is not None:
                    if len(new_channel.members) > 0:
                        await connecting(client, new_channel)

        self.voice_channel_for_mode_2 = new_channel





