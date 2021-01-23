import discord
import pyttsx3
import os
import csv
from config import settings, paths
from asyncio import sleep


def is_connected(client):
    if not client.voice_clients:
        return False

    else:
        if client.voice_clients[0].is_connected():
            return True
        else:
            return False


def connecting(client, given_channel):
    if is_connected(client):
        voice_client = client.voice_clients[0]
        if voice_client.channel != given_channel:
            await voice_client.disconnect()
            voice_client = await given_channel.connect()

    else:
        voice_client = await given_channel.connect()

    return voice_client


def disconnecting(client):
    if is_connected(client):
        voice_client = client.voice_clients[0]
        await voice_client.disconnect()


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


class ModeManager:
    def __init__(self):
        self.mode = 1
        self.voice_channel_for_mode_2 = None

    def get_mode(self):
        return self.mode

    def set_mode(self, client, new_mode):
        if is_connected(client) and self.mode != new_mode:
            voice_client = client.voice_clients[0]
            while voice_client.is_playing():
                await sleep(1)
            disconnecting(client)

        if new_mode == 2:
            if self.voice_channel_for_mode_2 is not None:
                if len(self.voice_channel_for_mode_2.members) > 0:
                    connecting(client, self.voice_channel_for_mode_2)

        self.mode = new_mode

    def set_voice_channel(self, client, new_channel):
        if self.mode == 2:
            if self.voice_channel_for_mode_2 != new_channel:
                if self.voice_channel_for_mode_2 is not None:
                    disconnecting(client)

                if new_channel is not None:
                    if len(new_channel.members) > 0:
                        connecting(client, new_channel)

        self.voice_channel_for_mode_2 = new_channel





