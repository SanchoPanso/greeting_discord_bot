from src.bot import GreetingBot
from os import getenv
from sys import exit


if __name__ == '__main__':

    bot_token = getenv("BOT_TOKEN")
    if not bot_token:
        exit("Error: no token provided")

    bot = GreetingBot()
    bot.run(bot_token)
