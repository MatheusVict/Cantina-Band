import discord
from discord.ext import commands
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

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} logged')

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
        if 1 <= selection <= 5:
            video_id = results[selection - 1]['id']['videoId']
            print(f'id do video {video_id}')

            if (ctx.voice_client):
                await ctx.voice_client.disconnect()

            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()

            # Use pytube to get the stream URL
            yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
            stream = yt.streams.filter(only_audio=True).first()
            url = stream.url
            voice_client.play(discord.FFmpegPCMAudio(url))
        else:
            await ctx.send("Invalid selection.")
    except asyncio.TimeoutError:
        await ctx.send('No selection made. Command timed out.')
    except ValueError:
        await ctx.send('Invalid selection. Please enter a valid number.')


@bot.command()
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if (voice_client and voice_client.is_playing()):
        voice_client.stop()
    await voice_client.disconnect()


bot.run(TOKEN)
