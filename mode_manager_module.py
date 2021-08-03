import asyncio
from connection_module import is_connected, connecting, disconnecting


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
