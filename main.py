from discord import Intents
from discord.ext.commands import Bot, MissingPermissions
import os
from os import listdir
from asyncio import run
from dotenv import load_dotenv

# from lib import setup

PREFIX = '$'
INTENTS = Intents.all()

load_dotenv()
TOKEN = os.getenv('SMOL_AME_TOKEN')
bot = Bot(command_prefix=PREFIX, intents=INTENTS)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

async def load():
    for filename in listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send("Sorry, but you do not have the permissions to use that command.")
    else:
        await ctx.send("ERROR: Something went wrong.")

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

if __name__ == "__main__":
    run(main())