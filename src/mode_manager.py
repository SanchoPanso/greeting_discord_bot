import asyncio
from src.connection import is_connected, connect, disconnect
from discord import Client, VoiceChannel, VoiceState, Member


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
            await disconnect(client)

        if new_mode == 2:
            if self.voice_channel_for_mode_2 is not None:
                if len(self.voice_channel_for_mode_2.members) > 0:
                    await connect(client, self.voice_channel_for_mode_2)

        self.mode = new_mode

    async def set_voice_channel(self, client: Client, new_channel: VoiceChannel):
        if self.mode == 2:
            if self.voice_channel_for_mode_2 != new_channel:
                if self.voice_channel_for_mode_2 is not None:
                    await disconnect(client)

                if new_channel is not None:
                    if len(new_channel.members) > 0:
                        await connect(client, new_channel)

        self.voice_channel_for_mode_2 = new_channel

    def bot_must_connect_and_play(self,
                                  client: Client,
                                  member: Member,
                                  before: VoiceState,
                                  after: VoiceState):

        if self.mode == 1:
            cond1 = before.channel is not after.channel
            cond2 = after.channel is not None
            cond3 = member.id != client.user.id
            cond4 = after.channel.guild.me.permissions_in(after.channel).connect if cond2 else False

            all_conditions_are_true = cond1 and cond2 and cond3 and cond4
            return all_conditions_are_true

        if self.mode == 2:
            if self.voice_channel_for_mode_2 is not None and member.id != client.user.id:
                if before.channel != self.voice_channel_for_mode_2:
                    if after.channel == self.voice_channel_for_mode_2:
                        return True

            return False

    def bot_must_disconnect(self,
                            before: VoiceState,
                            after: VoiceState):
        if self.mode == 1:
            return True

        elif self.mode == 2:
            if before.channel == self.voice_channel_for_mode_2:
                if after.channel != self.voice_channel_for_mode_2:
                    if self.voice_channel_for_mode_2 is not None:
                        if len(self.voice_channel_for_mode_2.members) == 1:
                            return True
            return False


