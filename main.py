import discord
from discord.ext import commands
import datetime
import os
import json
import requests
import tweepy
import dotenv
from dotenv import *
from discord_slash import *
from discord_slash.utils.manage_commands import *

client = commands.Bot(command_prefix='tc!', intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name=f"🕊️ | /link"))
slash = SlashCommand(client, sync_commands=True)
load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")
twitter_url = ["https://twitter.com", "https://fxtwitter.com"]

def get_id_from_url(tweet_url):
  tweet_url = tweet_url.split("https://")
  if len(tweet_url) == 2:
      tweet_url = tweet_url[1].split("twitter.com")
      if len(tweet_url) == 2:
          tweet_url = tweet_url[1].split("/")[3::3]
          tweet_url = tweet_url[0].split("?")[::]
          tweet_id = tweet_url[0]
          return tweet_id
      else:
          tweet_url = tweet_url[1].split("fxtwitter.com")
          tweet_url = tweet_url[1].split("/")[3::3]
          tweet_url = tweet_url[0].split("?")[::]
          tweet_id = tweet_url[0]
          return tweet_id
  else:
    return None

async def auth_process(channel):
  pins = await channel.pins()
  if len(pins) != 0:
    for message in pins:
      await message.unpin()
  async for msg in channel.history():
    if msg.author == client.user and msg.content.startswith("Twitter User Access Token") or msg.content.startswith("Twitter User Token"):
      await msg.edit(content = "[Cancelled] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  try:
    embed=discord.Embed(title = "🔗 Link Your Twitter Account", description = f"Please go to [Twitter API Authorize]({auth.get_authorization_url()}), click on \"Authorize app\", then send the verification PIN code here within 60 seconds.", color=0x3983f2)
    auth_msg = await channel.send(embed=embed)
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
      await channel.send(embed=embed)
    else:
      try:
        auth.get_access_token(pin_code_msg.content)
      except:
        embed=discord.Embed(title = "⚠️ Link Failed", description = "Unauthorized PIN code.", color=0xeca42c)
        embed.set_footer(text="ERR_UNAUTHORIZED")
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title = "✅ Account Linked", description = "You can unlink your account by using `/unlink`(`tc!unlink`) at any time.", color=0x3983f2)
        await channel.send(embed=embed)
        token_msg = await channel.send(f"Twitter User Access Token\n||`{auth.access_token}`||\n||`{auth.access_token_secret}`||")
        await token_msg.pin()

@client.event
async def on_ready():
  client.uptime = datetime.datetime.utcnow()
  print('<Logged in as {0.user}>'.format(client))

@client.event
async def on_raw_reaction_add(payload):
  message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
  emoji_list = ["❤️", "🔁", "📡"]
  if any(word in message.content for word in twitter_url) and get_id_from_url(message.content) != None:
    user = client.get_user(int(payload.user_id))
    if user != client.user:
      pins = await user.pins()
      link_notify_embed=discord.Embed(title = "ℹ️ You Haven't Linked Your Twitter Account Yet", description = f"Use `/link`(`tc!link`) to link your Twitter account, then you can use Discord reactions to like, retweet, and follow users.", color=0x3983f2)
      if (len(pins) == 0 or pins[0].content.startswith("Twitter User Access Token") == False) and str(payload.emoji) in emoji_list:
        try:
          await user.send(embed=link_notify_embed)
        except:
          pass
      if len(pins) != 0 and pins[0].content.startswith("Twitter User Access Token") and str(payload.emoji) in emoji_list:
        token_list = pins[0].content.split("\n")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = token_list[1].replace("`", "").replace("||", "")
        access_token_secret = token_list[2].replace("`", "").replace("||", "")
        auth.set_access_token(access_token, access_token_secret)
        twitter_client = tweepy.Client(bearer_token = bearer_token, consumer_key = consumer_key, consumer_secret = consumer_secret, access_token = access_token, access_token_secret = access_token_secret)
        if str(payload.emoji) == "❤️":
          try:
            twitter_client.like(get_id_from_url(message.content))
          except:
            pass
        if str(payload.emoji) == "🔁":
          try:
            twitter_client.retweet(get_id_from_url(message.content))
          except:
            pass
        if str(payload.emoji) == "📡":
          try:
            tweet = twitter_client.get_tweet(get_id_from_url(message.content), expansions='author_id')
            twitter_client.follow_user(tweet.includes['users'][0].id)
          except:
            pass

@client.event
async def on_raw_reaction_remove(payload):
  message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
  emoji_list = ["❤️", "🔁", "📡"]
  if any(word in message.content for word in twitter_url):
    user = client.get_user(int(payload.user_id))
    if user != client.user:
      pins = await user.pins()
      if len(pins) != 0 and str(payload.emoji) in emoji_list:
        if pins[0].content.startswith("Twitter User Access Token"):
          token_list = pins[0].content.split("\n")
          auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
          access_token = token_list[1].replace("`", "").replace("||", "")
          access_token_secret = token_list[2].replace("`", "").replace("||", "")
          auth.set_access_token(access_token, access_token_secret)
          tp_client = tweepy.Client(bearer_token = bearer_token, consumer_key = consumer_key, consumer_secret = consumer_secret, access_token = access_token, access_token_secret = access_token_secret)
          if str(payload.emoji) == "❤️":
            try:
              tp_client.unlike(get_id_from_url(message.content))
            except:
              pass
          if str(payload.emoji) == "🔁":
            try:
              tp_client.unretweet(get_id_from_url(message.content))
            except:
              pass
          if str(payload.emoji) == "📡":
            try:
              tweet = tp_client.get_tweet(get_id_from_url(message.content), expansions='author_id')
              tp_client.unfollow_user(tweet.includes['users'][0].id)
            except:
              pass

@client.event
async def on_message(message):
  if any(word in message.content for word in twitter_url) and get_id_from_url(message.content) != None:
    reaction_list = ["📡", "🔁", "❤️"]
    for i in reaction_list:
      await message.add_reaction(i)
      await asyncio.sleep(0.3)
  await client.process_commands(message)

@client.command()
async def ping(ctx):
  embed = discord.Embed(title=":ping_pong: Pong!", description=f"`{round(client.latency * 1000, 1)} ms`", color=0x3983f2)
  await ctx.send(embed=embed)

@slash.slash(description='Shows current ping')
async def ping(ctx):
  embed = discord.Embed(title=":ping_pong: Pong!", description=f"`{round(client.latency * 1000, 1)} ms`", color=0x3983f2)
  await ctx.send(embed=embed)

@client.command()
async def link(ctx):
  await auth_process(ctx.author)

@slash.slash(description="Link your Twitter account")
async def link(ctx):
  await ctx.send("Processing...", delete_after = 0.01)
  await auth_process(ctx.author)

@client.command()
async def unlink(ctx):
  try:
    pins = await ctx.author.pins()
  except:
    pass
  else:
    if len(pins) != 0:
      for message in pins:
        await message.unpin()
    async for msg in ctx.author.history():
      if msg.author == client.user and msg.content.startswith("Twitter User Access Token") or msg.content.startswith("Twitter User Token"):
        await msg.edit(content = "[Cancelled] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")
    embed=discord.Embed(title = "✅ Account Unlinked", description = "All messages containing user access keys have been overwritten.\n\nYou can revoke the permissions of this application in Twitter's [user settings](https://twitter.com/settings/connected_apps).", color=0x3983f2)
    await ctx.send(embed=embed)

@slash.slash(description="Unlink your Twitter account")
async def unlink(ctx):
  try:
    pins = await ctx.author.pins()
  except:
    pass
  else:
    if len(pins) != 0:
      for message in pins:
        await message.unpin()
    async for msg in ctx.author.history():
      if msg.author == client.user and msg.content.startswith("Twitter User Access Token") or msg.content.startswith("Twitter User Token"):
        await msg.edit(content = "[Cancelled] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")
    embed=discord.Embed(title = "✅ Account Unlinked", description = "All messages containing user access keys have been overwritten.\n\nYou can revoke the permissions of this application in Twitter's [user settings](https://twitter.com/settings/connected_apps).", color=0x3983f2)
    await ctx.send(embed=embed)

client.run(os.getenv("TOKEN"))