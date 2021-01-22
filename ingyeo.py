import os
import discord
from discord.ext import commands
import logging
import json

import sleep_log_analyze as sleeping


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open("config.json", "r") as f:
    config = json.load(f)

bot = commands.Bot(command_prefix='!')



@bot.command()
async def ping(ctx):
    await ctx.send(f'pong! {round(round(bot.latency, 4)*1000)}ms')

@bot.command()
async def channels(ctx, *args):
    for guild in bot.guilds:
        for channel in guild.channels:
            print(channel)
            print(channel.id)
    # await ctx.send(f'{ctx.author.name}')



@bot.command(name="수면기록")
async def sleep_24h(ctx, name=None):
    if not name:
        name = ctx.author.name
    await ctx.send(file=discord.File(sleeping.sleep_24h(name)))
    
@bot.command(name="수면통계")
async def sleep_stat(ctx, name=None):
    if not name:
        name = ctx.author.name
    await ctx.send(file=discord.File(sleeping.sleep_stat(name)))

@bot.command()
async def sleep_crawl(limit: int=100):
    import pandas as pd    
    import datetime
    channel = bot.get_channel(config["sleep_channel"])

    # load previous data & last logging time
    if os.path.exists("sleep_message.csv"):
        df_prev = pd.read_csv("sleep_message.csv")
        date_time_str = df_prev.time.iloc[-1]
        last_time = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S.%f")
    else:
        df_prev = pd.DataFrame(columns=['author','time','content'])
        last_time = None
        pass

    data = list()
    async for msg in channel.history(oldest_first=True, after=last_time, limit=10000):
        if " 취침" in msg.content and " 기상" in msg.content:
            data.append({'author': msg.author.name,'time': msg.created_at,'content': msg.content})

    df = df_prev.append(data,ignore_index=True, sort=False)
    df.to_csv('sleep_message.csv', index=False)
    sleeping.sleep_parser()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name) 
    print(bot.user.id)
    print('------')
    await sleep_crawl()
    

bot.run(config["bot_token"])


