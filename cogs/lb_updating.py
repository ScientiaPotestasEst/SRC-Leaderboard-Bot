from datetime import time, timezone
from discord import File
from discord.ext import tasks
from discord.ext.commands import Cog, command, has_permissions
from os import system, listdir, replace
from filecmp import cmp
import shelve

with shelve.open('./data/config') as db:
    update_channel = db['update_channel']
    CHANNEL_ID = db['channel_id']

utc = timezone.utc

# If no tzinfo is given then UTC is assumed.
times = time(hour=0, minute=0, second=0, tzinfo=utc)

class Updating(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lb_update.start()

    def cog_unload(self):
        self.lb_update.cancel()

    @tasks.loop(time=times)
    async def lb_update(self):
        for filename in listdir('./data/db'):
            if filename.endswith('Leaderboard.txt'):
                replace(f"./data/db/{filename}", f"./data/db/{filename.replace('.txt', '_old.txt')}")
        
        system('python ./lib/leaderboards.py')

        changes = []
        for filename in listdir('./data/db'):
                    if filename.endswith('Leaderboard.txt'):
                        changes.append(not cmp(f"./data/db/{filename}", f"./data/db/{filename.replace('.txt', '_old.txt')}"))

        if update_channel and any(changes):
            channel = self.bot.get_channel(CHANNEL_ID)
            await channel.purge(limit = 10)

            if not listdir('./data/db'):
                await channel.send("No leaderboards have been created.")
            else:
                for filename in sorted(listdir('./data/db')):
                    if filename.endswith('Leaderboard.txt'):
                        await channel.send(f"__**{filename.replace('_',' ')[:-4]}**__", file=File(f"./data/db/{filename}"))
    
    @command(name='leaderboard_update', aliases=['lb_update', 'update'])
    @has_permissions(administrator=True)
    async def update_leaderboard(self, ctx):
        msg = await ctx.send("Updating leaderboards...")

        for filename in listdir('./data/db'):
            if filename.endswith('Leaderboard.txt'):
                replace(f"./data/db/{filename}", f"./data/db/{filename.replace('.txt', '_old.txt')}")
        
        system('python ./lib/leaderboards.py')

        await msg.delete()
        await ctx.send("Leaderboards updated!")

        changes = []
        for filename in listdir('./data/db'):
                    if filename.endswith('Leaderboard.txt'):
                        changes.append(not cmp(f"./data/db/{filename}", f"./data/db/{filename.replace('.txt', '_old.txt')}"))

        if update_channel and any(changes):
            channel = self.bot.get_channel(CHANNEL_ID)
            await channel.purge(limit = 10)

            if not listdir('./data/db'):
                await channel.send("No leaderboards have been created.")
            else:
                for filename in sorted(listdir('./data/db')):
                    if filename.endswith('Leaderboard.txt'):
                        await channel.send(f"__**{filename.replace('_',' ')[:-4]}**__", file=File(f"./data/db/{filename}"))

    @Cog.listener()
    async def on_ready(self):
        print(" lb_updating.py loaded")

async def setup(bot):
    await bot.add_cog(Updating(bot))