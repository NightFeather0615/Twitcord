from asyncio.events import get_child_watcher
import discord
from discord.ext import commands
import datetime
import os
import json
import requests
import time
import tweepy
import dotenv
from dotenv import *
from discord_slash import *
from discord_slash.utils.manage_commands import *
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import *

client = commands.Bot(command_prefix='tc!', intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name=f"🕊️ | tc!link"))
slash = SlashCommand(client, sync_commands=True)
client.remove_command("help")
load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")
twitter_urls = ["https://twitter.com", "https://fxtwitter.com"]

def get_id_from_url(tweet_url):
  if any(word in tweet_url for word in twitter_urls) and tweet_url.find('status') != -1:
      if len(tweet_url.split("https://")) == 2:
          if tweet_url.find(twitter_urls[0]) != -1:
            url_location = tweet_url.find(twitter_urls[0])
          else:
            url_location = tweet_url.find(twitter_urls[1])
          tweet_url = tweet_url[url_location:]
          tweet_id = tweet_url[tweet_url.find('status') + 7:].split("?")[0]
          return tweet_id
  else: return None

async def link_account(user, catch_message = None):
  pins = await user.pins()
  if len(pins) != 0:
    for message in pins:
      await message.unpin()
  async for msg in user.history():
    if msg.author == client.user and msg.content.startswith("Twitter User Access Token") or msg.content.startswith("Twitter User Token"):
      await msg.edit(content = "[Cancelled] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")
  if catch_message != None:
    await catch_message.delete()
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  try:
    embed=discord.Embed(title = "🔗 Link Your Twitter Account", description = f"Please go to [Twitter API Authorize]({auth.get_authorization_url()}), click on \"Authorize app\", then send the verification PIN code here within 60 seconds.", color=0x3983f2)
    auth_msg = await user.send(embed=embed)
  except:
    pass
  else:
    def check(m):
      return m.author != auth_msg.author and m.channel == auth_msg.channel
    try:
      pin_code_msg = await client.wait_for(event="message", check=check, timeout=75.0)
    except asyncio.TimeoutError:
      embed=discord.Embed(title = "⚠️ Link Failed", description = "Authorization timeout, please try again.", color=0xeca42c)
      embed.set_footer(text="ERR_TIMEOUT")
      await user.send(embed=embed)
    else:
      try:
        auth.get_access_token(pin_code_msg.content)
      except:
        embed=discord.Embed(title = "⚠️ Link Failed", description = "Unauthorized PIN code.", color=0xeca42c)
        embed.set_footer(text="ERR_UNAUTHORIZED")
        await user.send(embed=embed)
      else:
        embed=discord.Embed(title = "✅ Account Linked", description = "You can unlink your account by using `/unlink`(`tc!unlink`) at any time.", color=0x3983f2)
        await user.send(embed=embed)
        token_msg = await user.send(f"Twitter User Access Token\n||`{auth.access_token}`||\n||`{auth.access_token_secret}`||")
        await token_msg.pin()

async def unlink_account(user, catch_message = None):
  pins = await user.pins()
  if len(pins) != 0:
    for message in pins:
      await message.unpin()
  async for msg in user.history():
    if msg.author == client.user and msg.content.startswith("Twitter User Access Token") or msg.content.startswith("Twitter User Token"):
      await msg.edit(content = "[Cancelled] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")
  if catch_message != None:
    await catch_message.delete()
  embed=discord.Embed(title = "✅ Account Unlinked", description = "All messages containing user access keys have been overwritten.\n\nYou can revoke the permissions of this application in Twitter's [user settings](https://twitter.com/settings/connected_apps).", color=0x3983f2)
  await user.send(embed=embed)

# async def create_tweet_process(ctx, text):
#   user = ctx.author
#   if user != client.user:
#     twitter_client = await get_twitter_client(user, True)
#     new_tweet = twitter_client.create_tweet(text=text)
#     tweet = twitter_client.get_tweet(new_tweet.data['id'], expansions='author_id')
#     await ctx.send(f"https://twitter.com/{tweet.includes['users'][0].username}/status/{new_tweet.data['id']}")

# async def download_image(user, tweet_id, medias):
#   is_media_available = True
#   index = 1
#   file_list = []

#   def write_image(media, index):
#     image_data = requests.get(media.url).content
#     file_name = f"./catch/{user.id}_{tweet_id}_{index}.png"
#     file_list.append(file_name)
#     with open(file_name, 'wb') as img_file:
#       img_file.write(image_data)

#   for media in medias:
#     if media.type != 'photo':
#       is_media_available = False

#   if is_media_available == True:
#     for media in medias:
#       if index >= 10: break
#       write_image(media, index)
#       index += 1

#   for file_name in file_list:
#     file = discord.File(file_name, filename=file_name)
#     await user.send(file=file)

async def ping_calc(ctx, msg, index):
  time_elsp = []
  ping_rec = []
  file_id = (str(datetime.datetime.now().timestamp()) + str(ctx.author.id) + str(ctx.channel.id)).replace(".", "")
  start_time = datetime.datetime.now().strftime('%H:%M:%S')
  for i in range(1, index+1):
    loading_dot = "." + "." * int(i % 3) + " " * int(5 - (i % 3))
    progress = ("■" * round(i/index*10)) + ("□" * (10 - round(i/index*10)))
    loading_animation = f"Tracking bot latency{loading_dot}{progress} {round(i/index*100, 1)}%"
    time_elsp.append(datetime.datetime.now().strftime('%H:%M:%S'))
    before = time.monotonic()
    await msg.edit(content = loading_animation)
    after = time.monotonic()
    ping_rec.append(round((after - before) * 1000, 1))
    await asyncio.sleep(1)
  end_time = time_elsp[index-1]
  max_ping = max(ping_rec)
  min_ping = min(ping_rec)
  avg_ping = round(sum(ping_rec) / index, 1)
  fig = plt.figure(figsize=(20, 10), facecolor="#303340")
  ax = plt.subplot(1,1,1)
  ax.plot(time_elsp, ping_rec, 'o-', c="#ffffff", markeredgecolor="#ffffff")
  ax.set_facecolor("#303340")
  ax.tick_params(axis = "x", colors="#3983f2", rotation=270)
  ax.tick_params(axis = "y", colors="#3983f2")
  ax.yaxis.grid(linestyle="--", linewidth = 0.5)
  ax.set_axisbelow(True)
  for pos in ['top', 'right', 'bottom', 'left']:
    ax.spines[pos].set_visible(False)
  fig = plt.gcf()
  plt.savefig(f"./catch/{file_id}.png")
  file = discord.File(f"./catch/{file_id}.png", filename="image.png")
  await msg.delete()
  embed = discord.Embed(title=f"📑 Latency record from {start_time} to {end_time}", description=f"Max: {max_ping} ms | Min: {min_ping} ms | Avg: {avg_ping} ms", color=0x3983f2)
  embed.set_image(url=f"attachment://image.png")
  embed.set_footer(text=f"Request by {ctx.author.name}#{ctx.author.discriminator}")
  await ctx.channel.send(embed=embed, file=file)
  os.remove(f"./catch/{file_id}.png")

async def get_twitter_client(user, notify:bool):
  pins = await user.pins()
  link_notify_embed=discord.Embed(title = "ℹ️ You Haven't Linked Your Twitter Account Yet", description = f"Use `/link`(`tc!link`) to link your Twitter account, then you can you can interact with Twitter in Discord.", color=0x3983f2)
  if (len(pins) == 0 or pins[0].content.startswith("Twitter User Access Token") == False) and notify == True:
    try:
      await user.send(embed=link_notify_embed)
    except: pass
  if len(pins) != 0 and pins[0].content.startswith("Twitter User Access Token"):
    token_list = pins[0].content.split("\n")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    access_token = token_list[1].replace("`", "").replace("||", "")
    access_token_secret = token_list[2].replace("`", "").replace("||", "")
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.Client(bearer_token = bearer_token, consumer_key = consumer_key, consumer_secret = consumer_secret, access_token = access_token, access_token_secret = access_token_secret)

@client.event
async def on_ready():
  client.uptime = datetime.datetime.utcnow()
  print('<Logged in as {0.user}>'.format(client))

@client.event
async def on_raw_reaction_add(payload):
  channel = client.get_channel(payload.channel_id)
  if channel != None:
    message = await channel.fetch_message(payload.message_id)
    if any(word in message.content for word in twitter_urls) and get_id_from_url(message.content) != None and str(payload.emoji) in ["❤️", "🔁", "📡"]:
      user = client.get_user(int(payload.user_id))
      if user != client.user:
        twitter_client = await get_twitter_client(user, True)
        if str(payload.emoji) == "❤️":
          try:
            twitter_client.like(get_id_from_url(message.content))
          except: pass
        if str(payload.emoji) == "🔁":
          try:
            twitter_client.retweet(get_id_from_url(message.content))
          except: pass
        if str(payload.emoji) == "📡":
          try:
            tweet = twitter_client.get_tweet(get_id_from_url(message.content), expansions='author_id')
            twitter_client.follow_user(tweet.includes['users'][0].id)
          except: pass
        # if str(payload.emoji) == "📥":
        #   try:
        #     tweet_id = get_id_from_url(message.content)
        #     tweet = twitter_client.get_tweet(tweet_id, expansions='attachments.media_keys', media_fields='url')
        #     medias = tweet.includes['media']
        #     await download_image(user, tweet_id ,medias)
        #   except: pass

@client.event
async def on_raw_reaction_remove(payload):
  channel = client.get_channel(payload.channel_id)
  if channel != None:
    message = await channel.fetch_message(payload.message_id)
    if any(word in message.content for word in twitter_urls) and get_id_from_url(message.content) != None and str(payload.emoji) in ["❤️", "🔁", "📡"]:
      user = client.get_user(int(payload.user_id))
      if user != client.user:
        twitter_client = await get_twitter_client(user, False)
        if str(payload.emoji) == "❤️":
          try:
            twitter_client.unlike(get_id_from_url(message.content))
          except: pass
        if str(payload.emoji) == "🔁":
          try:
            twitter_client.unretweet(get_id_from_url(message.content))
          except: pass
        if str(payload.emoji) == "📡":
          try:
            tweet = twitter_client.get_tweet(get_id_from_url(message.content), expansions='author_id')
            twitter_client.unfollow_user(tweet.includes['users'][0].id)
          except: pass

@client.event
async def on_message(message):
  if any(word in message.content for word in twitter_urls) and get_id_from_url(message.content) != None and isinstance(message.channel, discord.DMChannel) == False:
    for i in ["📡", "🔁", "❤️"]:
      try:
        await message.add_reaction(i)
      except: pass
      await asyncio.sleep(0.3)
  await client.process_commands(message)

@client.command()
async def invite(ctx):
  embed=discord.Embed(title = "", description = f"Click [here](https://discord.com/oauth2/authorize?client_id=917122425102163971&permissions=412317248576&scope=bot%20applications.commands) to invite <@!{client.user.id}> to your server!", color=0x3983f2)
  await ctx.send(embed=embed)

@slash.slash(description="Show invite link")
async def invite(ctx):
  embed=discord.Embed(title = "", description = f"Click [here](https://discord.com/oauth2/authorize?client_id=917122425102163971&permissions=412317248576&scope=bot%20applications.commands) to invite <@!{client.user.id}> to your server!", color=0x3983f2)
  await ctx.send(embed=embed)

@client.command()
async def ping(ctx, index=None):
  if index == None: index = 10
  try:
    index = int(index)
  except:
    embed=discord.Embed(title = "⚠️ Command Failed", description = "Invalid integer.\n`tc!ping <index(1~60)>`", color=0xeca42c)
    embed.set_footer(text="ERR_BADARGUMENT")
    await ctx.send(embed=embed)
  if type(index) == int:
    if 0 < index <= 60:
      msg = await ctx.send("Tracking bot latency...   □□□□□□□□□□ 0.0%")
      await ping_calc(ctx, msg, index)
    else:
      embed=discord.Embed(title = "⚠️ Command Failed", description = "Index out of range(1~60).\n`tc!ping <index(1~60)>`", color=0xeca42c)
      embed.set_footer(text="ERR_INVALIDVALUE")
      await ctx.send(embed=embed)

@slash.slash(description="Track bot latency")
async def ping(ctx, index:int=10):
  if 0 < index <= 60:
    msg = await ctx.send("Tracking bot latency...   □□□□□□□□□□ 0.0%")
    await ping_calc(ctx, msg, index)
  else:
    embed=discord.Embed(title = "⚠️ Command Failed", description = "Index out of range(1~60).\n`/ping <index(1~60)>`", color=0xeca42c)
    embed.set_footer(text="ERR_INVALIDVALUE")
    await ctx.send(embed=embed)
    
@client.command()
async def link(ctx):
  await link_account(ctx.author)

@slash.slash(description="Link your Twitter account")
async def link(ctx):
  catch_message = await ctx.send("Processing...")
  await link_account(ctx.author, catch_message)

@client.command()
async def unlink(ctx):
  await unlink_account(ctx.author)

@slash.slash(description="Unlink your Twitter account")
async def unlink(ctx):
  catch_message = await ctx.send("Processing...")
  await unlink_account(ctx.author, catch_message)

client.run(os.getenv("TOKEN"))
