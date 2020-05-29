import os, discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(aliases=['off', 'shutdown'])
async def close(ctx):
    try:
        await bot.close()
        print('Bot shutdown.')
    except:
        pass

@bot.command()
async def join(ctx):
    await ctx.author.voice.channel.connect()
    print(f'{bot.user} joined {bot.voice_clients[0].channel}')

@bot.command()
async def leave(ctx):
    print(f'{bot.user} leaving {bot.voice_clients[0].channel}')
    await ctx.guild.voice_client.disconnect()

@bot.command(aliases=['rl'])
async def reload_ext(ctx, extension):
    try:
        bot.reload_extension(f'cogs.{extension}')
        print(f'{extension} successfully reloaded.')
    except Exception as error:
        print(f'{extension} failed to reload. [{error}]')

@bot.command()
async def load_ext(ctx, extension):
    try:
        bot.load_extension(f'cogs.{extension}')
        print(f'{extension} successfully loaded.')
    except Exception as error:
        print(f'{extension} could not be loaded. [{error}]')

@bot.command()
async def unload_ext(ctx, extension):
    try:
        bot.unload_extension(f'cogs.{extension}')
        print(f'{extension} successfully unloaded.')
    except Exception as error:
        print(f'{extension} could not be unloaded. [{error}]')

for f in os.listdir('./cogs'):
    if (f.endswith('.py')):
        bot.load_extension(f'cogs.{f[:-3]}')

bot.run(TOKEN)