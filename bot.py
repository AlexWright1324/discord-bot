import discord
from discord.ext import commands
import asyncio

import yt_dlp

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

import urllib
import requests
from bs4 import BeautifulSoup

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)
client.remove_command('help')

links_array = []
deck_links_array = []
song_queue = []

@client.check
async def _log(ctx):
    print(f"{ctx.author.name}: {ctx.message.content}")
    return True

def log(message):
    print(f"  -- {message}")

def is_mod():
    async def inner(ctx):
        mods = {"Jamie" : 276798056702279680,}
                #"Alex"  : 277424518266355712}
        if ctx.author.id in mods.values():
            return True
        else:
            log(f"{ctx.author.name} is not a moderator")
            return False
    return commands.check(inner)

"""
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        log(f'Exception in {ctx.command}: {error}')
"""

@is_mod()
@client.hybrid_command(name="test")
async def _command(ctx):
    async with ctx.typing():
        await ctx.send("Tested!!")

@client.hybrid_command(name="help")
async def _command(ctx):
    async with ctx.typing():
        with open("Commands.txt", "r") as r:
            helps = r.read()
            await ctx.send(helps)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@client.hybrid_command(name="play")
async def _play(ctx, *, search_keywords):
    async with ctx.typing():
        search_keywords = search_keywords.replace("shorts/","watch?v=")

        player = await YTDLSource.from_url(search_keywords, loop=client.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    
    await ctx.reply(f"Now playing: {player.title}")

@client.hybrid_command(name="stop")
async def _leave(ctx):
    if (ctx.voice_client): # If the bot is in a voice channel 
        await ctx.guild.voice_client.disconnect() # Leave the channel
        await ctx.send('Bot left')
    else: # But if it isn't
        await ctx.send("I'm not in a voice channel, use the join command to make me join")

@_play.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise log("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

@client.hybrid_command(name="requirements")
async def _command(ctx, *, arg):
    global links_array
    url = "https://store.steampowered.com/search/?term="+arg
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a")
    for link in links:
        #print(link.get("href"))
        links_array.append(link.get("href"))
    for element in links_array:
        if element.startswith("https://store.steampowered.com/app/"):
            game_link = element
            #print(game_link)
            break
    url = game_link
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    my_div = soup.find("div", {"class": "game_page_autocollapse sys_req"})
    #print(my_div)
    my_text = my_div.get_text(separator="\n")
    my_text = "**"+soup.head.title.string.replace(" on Steam","")+"** "+my_text
    if "macOS" in my_text:
        my_text = my_text.replace('Windows','Operating Systems:\n						Windows', 1)
        my_text = my_text.replace('Minimum:','\nMinimum:')
    my_text = my_text.replace('\n\n\n\n\n', '')
    await ctx.send(my_text.replace("System Requirements","**System Requirements**\n"))
    links_array = []

@client.hybrid_command(name="steamdeck")
async def _command(ctx, *, arg):
    global deck_links_array
    deck_links_array = []
    url = "https://store.steampowered.com/search/?term="+arg
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    links2 = soup.find_all("a")
    for link in links2:
        #print(link.get("href"))
        deck_links_array.append(link.get("href"))
    for element in deck_links_array:
        if element.startswith("https://store.steampowered.com/app/"):
            game_link = element
            #print(game_link)
            break
    url = game_link
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    options = Options()
    options.add_argument('--disable-extensions')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-window')
    driver = uc.Chrome(options=options)
    driver.get(url)
    try:
        try:
            dropdown = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'ageYear'))))
            dropdown.select_by_visible_text("1987")
            dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'view_product_page_btn')))
            dropdown.click()
        except:
            #print("No Age Check")
            pass
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div[2]/div[1]')))
            element.click()

        except:
            #print("No Cookies")
            pass
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.deckverified_BannerContainer_2b4eh')))
        element.screenshot('steam compatibility.png')

        driver.quit()
        
        with open('steam compatibility.png', 'rb') as f:
            image = discord.File(f)
            await ctx.send(soup.head.title.string.replace(" on Steam",""), file=image)
    except:
        await ctx.send("Steam Deck Compatibility not found, try again or type a new different game.")
        driver.quit()

@client.hybrid_command(name="news")
async def _command(ctx, *, arg):
    global news_links_array
    news_links_array = []
    url = "https://store.steampowered.com/search/?term="+arg
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    links3 = soup.find_all("a")
    for link in links3:
        #print(link.get("href"))
        news_links_array.append(link.get("href"))
    for element in news_links_array:
        if element.startswith("https://store.steampowered.com/app/"):
            game_link = element.replace("https://store.steampowered.com/app/","https://store.steampowered.com/news/app/")
            game_link = game_link[:47]
            #print(game_link)
            break
    url = game_link
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    options = Options()
    for arg in ['--disable-extensions', '--headless', '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage', '--no-window']:
        options.add_argument(arg)
    driver = uc.Chrome(options=options)
    driver.get(url)
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[7]/div[6]/div/div[2]/div/div/div[2]/div[2]/div/div[*]/div/div[2]/div/a/div/div/div[1]')))
        element.click()
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div/div[2]/div[1]')))
            element.click()
        except:
            #print("No Cookies")
            pass
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[2]/div/div/div/div[2]/div[2]/div[1]')))
        news_height = element.size['height']
        driver.set_window_size(1024, news_height)
        element.screenshot('news.png')

        driver.quit()
        
        with open('news.png', 'rb') as f:
            image = discord.File(f)
            await ctx.send(soup.head.title.string.replace(" on Steam",""), file=image)
    except:
        await ctx.send("No Older Posts Found, try a different game.")
        driver.quit()

@client.hybrid_command(name="stablediffusion")
async def _command(ctx, _arg):
    result = False
    tries = 0
    url = "https://stablediffusionweb.com/#demo"
    options = Options()
##        options.add_argument('--disable-extensions')
##        options.add_argument('--headless')
##        options.add_argument('--disable-gpu')
##        options.add_argument('--no-sandbox')
##        options.add_argument('--disable-dev-shm-usage')
##        options.add_argument('--no-window')
    driver = uc.Chrome(options=options)
    driver.get(url)
    iframe = driver.find_element(By.TAG_NAME, "iframe")
    driver.switch_to.frame(iframe)
    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="prompt-text-input"]/label/input')))
    element.send_keys(ctx.content.replace("!stablediffusion ", "")+"\n")          
    processing = await ctx.send("Processing using Stable Diffusion... (may take up to 2 mins to process)")
    while tries < 6:
        try:
            if result == True:
                await processing.edit(content="Result Recieved!")
                break   
            else:
                div_section = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH, '//*[@id="gallery"]/div[2]/div')))
                image_elements = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.TAG_NAME, 'img')))
                for i, img in enumerate(image_elements):
                    # get the image source URL
                    img_url = img.get_attribute('src')

                    # send a GET request to download the image
                    response = requests.get(img_url)

                    # write the image to a local file
                    with open(f'image_{i}.jpg', 'wb') as f:
                        f.write(response.content)
                f.close()
                result = True
        except:
            tries = tries + 1
            await processing.edit(content=str(tries)+"/6 tries")


with open("client.secret", "r") as file:
    client_secret = file.read()

client.run(client_secret)
