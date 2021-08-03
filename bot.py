import discord
from discord.ext import commands
from config import settings

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=settings['prefix'],
                   intents=intents)

