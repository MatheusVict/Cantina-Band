import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
from pytube import YouTube

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

bot.remove_command('help')

queue = []

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} logged')

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title = 'Bot commands',
        description = 'Welcome to the help section. Here are all the commands for your fun!',
        color = discord.Color.dark_orange()
    )

    embed.set_thumbnail(url='https://github.com/MatheusVict/Cantina-Band/assets/103688000/d04afde8-b608-490a-a30f-7da2903b2353')

    embed.add_field(
        name = '!help',
        value = 'List all of the commands',
        inline = False
    )

    embed.add_field(
        name = '!play <Your song>',
        value = 'Play a song with name and add to your queue',
        inline = False
    )
    embed.add_field(
        name = '!skip',
        value = 'Skip to next music of queue',
        inline = False
    )
    embed.add_field(
        name = '!pause',
        value = 'Pause your queue',
        inline = False
    )
    embed.add_field(
        name = '!resume',
        value = 'Resume your queue',
        inline = False
    )
    embed.add_field(
        name = '!stop',
        value = 'Stop bot',
        inline = False
    )

    await ctx.send(embed=embed)

@bot.command()
async def play(ctx, *, query):
    # Search for videos using the YouTube Data API
    search_url = f'https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&part=snippet&type=video&q={query}'
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            data = await response.json()

    # Extract the video IDs and titles of the top 5 search results
    results = data['items'][:5]
    options = '\n'.join([f'{i+1}. {result["snippet"]["title"]}' for i, result in enumerate(results)])
    await ctx.send(f'Top 5 search results:\n{options}\n\nPlease enter the number corresponding to the song you want to play.')

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        selection_msg = await bot.wait_for('message', check=check, timeout=60)
        selection = int(selection_msg.content)
        if (1 <= selection <= 5):
            video_id = results[selection - 1]['id']['videoId']
            print(f'id do video {video_id}')

            voice_channel = ctx.author.voice.channel
            voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

            if (voice_client and voice_client.is_playing()):
                # Add the selected video to the queue
                queue.append((video_id, ctx))
                await ctx.send('Song added to the queue.')
            else:
                # Play the selected video directly
                await play_song(video_id, ctx)
        else:
            await ctx.send("Invalid selection.")
    except asyncio.TimeoutError:
        await ctx.send('No selection made. Command timed out.')
    except ValueError:
        await ctx.send('Invalid selection. Please enter a valid number.')

@bot.command()
async def skip(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice_client and voice_client.is_playing()):
        voice_client.stop()
        if (queue):
            next_song = queue.pop(0)
            await play_song(next_song[0], next_song[1])
            await ctx.send('Skipped music. Playing the next song in the queue.')
        else:
            await ctx.send('Skipped music. There are no more songs in the queue.')
    else:
        await ctx.send("I'm not playing any music.")

@bot.command()
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if(voice_client and voice_client.is_playing()):
        voice_client.pause()
        await ctx.send("Music paused.")
    else:
        await ctx.send("I'm not playing any music.")

@bot.command()
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice_client and voice_client.is_paused()):
        voice_client.resume()
        await ctx.send("Music resumed.")
    else:
        await ctx.send("I'm not playing any paused music.")

@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice_client and voice_client.is_playing()):
        voice_client.stop()
    await voice_client.disconnect()

@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title = 'Bot infos',
        description = 'Thanks to use my bot. You can contact me clicking in my name',
        color = discord.Color.dark_orange()
    )

    embed.set_author(name='Matheus', url='https://github.com/MatheusVict', icon_url='https://avatars.githubusercontent.com/u/103688000?v=4')
    await ctx.send(embed=embed)

async def play_song(video_id, ctx):
    voice_channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if (voice_client):
        await voice_client.disconnect()

    voice_client = await voice_channel.connect()

    # Use pytube to get the stream URL
    yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
    stream = yt.streams.filter(only_audio=True).first()
    url = stream.url

    def play_next_song(error=None):
        if (error):
            print(f'Error playing song: {error}')
        
        if (queue):
            next_song = queue.pop(0)
            asyncio.run_coroutine_threadsafe(play_song(next_song[0], next_song[1]), bot.loop)

    voice_client.play(discord.FFmpegPCMAudio(url), after=play_next_song)

bot.run(TOKEN)
