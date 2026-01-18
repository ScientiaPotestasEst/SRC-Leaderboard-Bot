from discord import File
from discord.ext.commands import Cog, command
from os import listdir
from os.path import isfile

class Posting(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command(name='leaderboard_FG', aliases=['lb_FG', 'FG'])
    async def post_FG_leaderboard(self, ctx):
        if isfile("./data/db/Full_Game_Leaderboard.png"):
            await ctx.send("__**Full Game Leaderboard**__", file=File("./data/db/Full_Game_Leaderboard.png"))
        else:
            await ctx.send("This leaderboard does not exist.")
    
    @command(name='leaderboard_IL', aliases=['lb_IL', 'IL'])
    async def post_IL_leaderboard(self, ctx):
        if isfile("./data/db/Individual_Levels_Leaderboard.png"):
            await ctx.send("__**Individual Levels Leaderboard**__", file=File("./data/db/Individual_Levels_Leaderboard.png"))
        else:
            await ctx.send("This leaderboard does not exist.")
    
    @command(name='leaderboard_ranking', aliases=['lb_ranking', 'ranking'])
    async def post_ranking_leaderboard(self, ctx):
        if isfile("./data/db/Ranking_Leaderboard.png"):
            await ctx.send("__**Ranking Leaderboard**__", file=File("./data/db/Ranking_Leaderboard.png"))
        else:
            await ctx.send("This leaderboard does not exist.")
    
    @command(name='leaderboard_all', aliases=['lb_all', 'all'])
    async def post_all_leaderboards(self, ctx):
        if not listdir('./data/db'):
            await ctx.send("No leaderboards have been created.")
        else:
            for filename in sorted(listdir('./data/db')):
                if filename.endswith('Leaderboard.png'):
                    await ctx.send(f"__**{filename.replace('_',' ')[:-4]}**__", file=File(f"./data/db/{filename}"))
    
    @Cog.listener()
    async def on_ready(self):
        print(" lb_posting.py loaded")

async def setup(bot):
    await bot.add_cog(Posting(bot))