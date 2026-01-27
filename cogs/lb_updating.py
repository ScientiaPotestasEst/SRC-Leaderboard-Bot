from datetime import time, timezone
from discord import File
from discord.ext import tasks
from discord.ext.commands import Cog, command, has_permissions
import os
from os import listdir, replace
from filecmp import cmp
import shelve
from lib import leaderboards

with shelve.open('./data/config') as db:
    update_channel = db['update_channel']
    CHANNEL_ID = db['channel_id']

utc = timezone.utc
DB_PATH = os.path.join("data", "db")

class Updating(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lb_update.start()

    def cog_unload(self):
        self.lb_update.cancel()

    def get_lb_files(self):
        """Yields tuples of (current_file_path, old_file_path, filename)"""
        for filename in listdir(DB_PATH):
            if filename.endswith('Leaderboard.png'):
                current_path = os.path.join(DB_PATH, filename)
                old_path = os.path.join(DB_PATH, filename.replace('.png', '_old.png'))
                yield current_path, old_path, filename

    def create_backup_of_current_lb(self):
        for current, old, _ in self.get_lb_files():
            replace(current, old)

    async def send_new_lb_if_changed(self):
        changes = []
        for current, old, _ in self.get_lb_files():
            if os.path.exists(old):
                changes.append(not cmp(current, old))
            else:
                changes.append(True)

        if update_channel and any(changes):
            channel = self.bot.get_channel(CHANNEL_ID)
            await channel.purge(limit = 10)

            if not listdir(DB_PATH):
                await channel.send("No leaderboards have been created.")
            else:
                # Sort the generator results by the filename (the 3rd item in our yield)
                lbs = sorted(self.get_lb_files(), key=lambda x: x[2])

                if not lbs:
                    await channel.send("No leaderboards have been created.")
                else:
                    for current_path, _, filename in lbs:
                        # Clean up name: remove underscores and the '.png' extension
                        title = filename.replace('_', ' ').replace('.png', '')
                        await channel.send(f"__**{title}**__", file=File(current_path))

    @tasks.loop(minutes=5)
    async def lb_update(self):
        self.create_backup_of_current_lb()
        
        leaderboards.update_leaderboards()

        await self.send_new_lb_if_changed()
    
    @command(name='leaderboard_update', aliases=['lb_update', 'update'])
    @has_permissions(administrator=True)
    async def update_leaderboard(self, ctx):
        msg = await ctx.send("Updating leaderboards...")

        self.create_backup_of_current_lb()
        
        leaderboards.update_leaderboards()

        await self.send_new_lb_if_changed()

        await msg.delete()
        await ctx.send("Leaderboards updated!")

    @Cog.listener()
    async def on_ready(self):
        print(" lb_updating.py loaded")

async def setup(bot):
    await bot.add_cog(Updating(bot))