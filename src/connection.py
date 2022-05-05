from discord import Client, VoiceChannel
import asyncio


def is_connected(client: Client):
    if not client.voice_clients:
        return False

    else:
        if client.voice_clients[0].is_connected():
            return True
        else:
            return False


async def connect(client: Client, given_channel: VoiceChannel):
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


async def disconnect(client: Client):
    if is_connected(client):
        voice_client = client.voice_clients[0]

        while voice_client.is_playing():
            await asyncio.sleep(1)

        await voice_client.disconnect()


