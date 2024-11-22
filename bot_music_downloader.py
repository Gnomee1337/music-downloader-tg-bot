import logging
import time
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputMediaAudio, InputFile, BufferedInputFile
from aiogram.filters import Command
from youtube_search import YoutubeSearch
from sclib import SoundcloudAPI, Track, Playlist
import io
from yt_dlp import YoutubeDL
import yt_dlp
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher()

# SoundCloud Client
sc_api = SoundcloudAPI()


def get_youtube_results(query):
    results = YoutubeSearch(query, max_results=5).to_dict()
    return results


async def download_youtube_audio(url: str) -> BufferedInputFile:
    # Configure yt-dlp options to stream directly to memory
    ydl_opts = {
        'format': 'bestaudio/best',  # Best available audio
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,  # Suppress verbose output
        'noprogress': True,  # Disable progress output
        'extractaudio': True,  # Extract audio only
        'audioquality': 1,  # Best audio quality
        'outtmpl': 'downloads/%(id)s.%(ext)s',  # Temporary file name (to be replaced later)
        'writeinfojson': False,  # Don't write info.json file
        'socket_timeout': 60,  # Timeout setting
    }
    buffer = io.BytesIO()  # Create a buffer to hold the audio data in memory
    try:
        # Use yt-dlp to download and process the YouTube video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and convert the audio
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace('.webm', '.mp3')
            video_title = info.get('title', 'Unknown Title')
            # Ensure the file exists and is valid
            if not filename or not os.path.exists(filename):
                raise ValueError("Failed to download the audio file.")
            # Read the downloaded file into the buffer
            with open(filename, 'rb') as f:
                buffer.write(f.read())
            # Clean up the temporary file
            os.remove(filename)
        # Check if buffer has data
        if buffer.getbuffer().nbytes == 0:
            raise ValueError("Download failed or file is empty.")
        if buffer.getbuffer().nbytes > 50 * 1024 * 1024:
            raise ValueError("File size exceeds 50 MB limit.")
        buffer.seek(0)  # Reset the buffer pointer to the beginning
        return BufferedInputFile(file=buffer.getvalue(), filename=f"{video_title}.mp3")
    except Exception as e:
        raise ValueError(f"Failed to process the YouTube URL: {e}")


# async def download_soundcloud_audio(url):
#     # Configure yt-dlp options to stream directly to memory
#     ydl_opts = {
#         'format': 'bestaudio/best',  # Best available audio
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'quiet': True,  # Suppress verbose output
#         'noprogress': True,  # Disable progress output
#         'extractaudio': True,  # Extract audio only
#         'audioquality': 1,  # Best audio quality
#         'outtmpl': 'downloads/%(id)s.%(ext)s',  # Temporary file name (to be replaced later)
#         'writeinfojson': False,  # Don't write info.json file
#         'socket_timeout': 60,  # Timeout setting
#     }
#     buffer = io.BytesIO()  # Create a buffer to hold the audio data in memory
#     try:
#         # Use yt-dlp to download and process the YouTube video
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             # Download and convert the audio
#             info = ydl.extract_info(url, download=True)
#             filename = ydl.prepare_filename(info).replace('.webm', '.mp3')
#             video_title = info.get('title', 'Unknown Title')
#             # Ensure the file exists and is valid
#             if not filename or not os.path.exists(filename):
#                 raise ValueError("Failed to download the audio file.")
#             # Read the downloaded file into the buffer
#             with open(filename, 'rb') as f:
#                 buffer.write(f.read())
#             # Clean up the temporary file
#             os.remove(filename)
#         # Check if buffer has data
#         if buffer.getbuffer().nbytes == 0:
#             raise ValueError("Download failed or file is empty.")
#         if buffer.getbuffer().nbytes > 50 * 1024 * 1024:
#             raise ValueError("File size exceeds 50 MB limit.")
#         buffer.seek(0)  # Reset the buffer pointer to the beginning
#         return BufferedInputFile(file=buffer.getvalue(), filename=f"{video_title}.mp3")
#     except Exception as e:
#         raise ValueError(f"Failed to process the YouTube URL: {e}")

async def download_soundcloud_audio(url):
    try:
        # URL for the soundcloudmp3.org site
        base_url = "https://soundcloudmp3.org/"

        # # Send a GET request to the website with the track URL
        # response = requests.get(base_url, params={'url': url})
        #
        # # Check if the response is successful
        # if response.status_code != 200:
        #     raise ValueError("Failed to fetch SoundCloud track data.")
        #
        # # Parse the HTML content of the page
        # soup = BeautifulSoup(response.content, 'html.parser')
        #
        # # Find the download link in the page (it's in a <a> tag with class 'btn btn-success')
        # download_button = soup.find('a', class_='btn btn-success')
        # if download_button:
        #     download_url = download_button.get('href')
        #
        #     # Fetch the track via the download URL
        #     track_response = requests.get(download_url)
        #     if track_response.status_code == 200:
        #         # Write the audio content to a file (or return it as bytes)
        #         filename = url.split('/')[-1] + '.mp3'  # You can change the filename strategy
        #         with open(filename, 'wb') as f:
        #             f.write(track_response.content)
        #         print(f"Track downloaded as {filename}")
        #     else:
        #         raise ValueError("Failed to download the track.")
        # else:
        #     raise ValueError("Download link not found on the page.")
    except Exception as e:
        print(f"Error: {e}")


# Command handler for '/start' and '/help'
@dp.message(Command('start'))
@dp.message(Command('help'))
async def send_welcome(message: types.Message):
    await message.reply("Hello! Send a track name or a direct SoundCloud/YouTube link to download a track.")


# Message handler for links or track names
@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()
    if 'soundcloud.com' in text:  # SoundCloud link
        await message.reply("Processing SoundCloud link...")
        try:
            file = await download_soundcloud_audio(text)
            await bot.send_audio(message.chat.id, audio=file)
        except Exception as e:
            await message.reply(f"Error: {str(e)}")
    elif 'youtube.com' in text:  # YouTube link
        await message.reply("Processing YouTube link...")
        try:
            file = await download_youtube_audio(text)
            await bot.send_audio(message.chat.id, audio=file)
        except Exception as e:
            await message.reply(f"Error: {str(e)}")
    else:  # Search for tracks
        await message.reply("Searching for the track...")
        yt_results = get_youtube_results(text)
        # sc_results = sc_client.search_tracks(text)

        # Send results to user
        inline_buttons = []
        for idx, result in enumerate(yt_results, start=1):
            # Construct the full URL for YouTube video
            full_url = f"https://www.youtube.com{result['url_suffix']}"

            # Now, check if 'youtube' is in the URL
            inline_buttons.append(types.InlineKeyboardButton(
                text=f"{idx}. YouTube: {result['title']}",
                callback_data=f"yt_{full_url}"
            ))
            # if 'youtube' in result['url']:
            #     inline_buttons.append(types.InlineKeyboardButton(
            #         text=f"{idx}. YouTube: {result['title']}",
            #         callback_data=f"yt_{result['url']}"
            #     ))
            # else:
            #     inline_buttons.append(types.InlineKeyboardButton(
            #         text=f"{idx}. SoundCloud: {result['title']}",
            #         callback_data=f"sc_{result['url']}"
            #     ))

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(*inline_buttons)
        await message.reply("Select a track to download", reply_markup=markup)


# Callback handler for inline button presses
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    url = callback_query.data.split('_')[1]
    if 'youtube' in url:
        await callback_query.answer("Downloading YouTube track...")
        file = await download_youtube_audio(url)
        await bot.send_audio(callback_query.from_user.id, file)
    else:
        await callback_query.answer("Downloading SoundCloud track...")
        file = await download_soundcloud_audio(url)
        await bot.send_audio(callback_query.from_user.id, file)


if __name__ == '__main__':
    dp.run_polling(bot)
