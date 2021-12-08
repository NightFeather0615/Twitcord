import discord
from discord import activity
from discord.ext import commands, tasks
import datetime
import os
import json
import requests
import tweepy
from discord_slash import *
from discord_slash.utils.manage_commands import *
from discord_components import *
from itertools import *

client = commands.Bot(command_prefix='tc!', intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name=f"🕊️ | /link(tc!link)"))
slash = SlashCommand(client, sync_commands=True)

consumer_key = "QI2PdLu5ewUDlDr41tSsrvzDo"
consumer_secret="EzP5PtU5omjlTAHS71jF20m9KhifyZwbOxGpso5wnQMgV4olSz"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAGZGWgEAAAAAnoGIiO%2B4fAh2BQC0Vc2yGw8uEmA%3DEWgL9g7KNbn5N7eyZd3v4JoZhbwKeFL8wOw3LvrCt8sYcHXkCE"
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
    embed=discord.Embed(title = "🔗 綁定Twitter帳號", description = f"請前往[Twitter API Authorize]({auth.get_authorization_url()})，登入並點擊\"Authorize app\"後，於60秒內將驗證PIN碼發送至此處。", color=0x3983f2)
    auth_msg = await channel.send(embed=embed)
  except:
    pass
  else:
    def check(m):
      return m.author != auth_msg.author and m.channel == auth_msg.channel
    try:
      pin_code_msg = await client.wait_for(event="message", check=check, timeout=75.0)
    except asyncio.TimeoutError:
      embed=discord.Embed(title = "⚠️ 操作失敗", description = "等候逾時，請重新嘗試。", color=0xeca42c)
      embed.set_footer(text="ERR_TIMEOUT")
      await channel.send(embed=embed)
    else:
      try:
        auth.get_access_token(pin_code_msg.content)
      except:
        embed=discord.Embed(title = "⚠️ 操作失敗", description = "綁定失敗，憑證遭拒。", color=0xeca42c)
        embed.set_footer(text="ERR_UNAUTHORIZED")
        await channel.send(embed=embed)
      else:
        embed=discord.Embed(title = "✅ 綁定成功", description = "為確保你的資訊安全，機器人不會儲存你的資料，而是在你進行反應時從私人訊息釘選抓取金鑰，請不要隨意釘選/解釘訊息。\n\n你隨時可以透過`/link`(`tc!unlink`)註銷。\n\n**如因Discord帳號遭盜用導致資料外洩，開發者不負任何責任，請自行承擔損失。**", color=0x3983f2)
        await channel.send(embed=embed)
        token_msg = await channel.send(f"Twitter User Access Token\n||`{auth.access_token}`||\n||`{auth.access_token_secret}`||")
        await token_msg.pin()

@client.event
async def on_ready():
  client.uptime = datetime.datetime.utcnow()
  DiscordComponents(client)
  print('<Logged in as {0.user}>'.format(client))

@client.event
async def on_raw_reaction_add(payload):
  message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
  emoji_list = ["❤️", "🔁", "📡"]
  if any(word in message.content for word in twitter_url) and get_id_from_url(message.content) != None:
    user = client.get_user(int(payload.user_id))
    if user != client.user:
      pins = await user.pins()
      link_notify_embed=discord.Embed(title = "ℹ️ 你尚未綁定Twitter帳號", description = f"輸入`/link`(`tc!link`)來綁定Twitter帳號，方可使用Discord反應來喜歡、轉推或追蹤作者。", color=0x3983f2)
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

@slash.slash(description='檢查延遲')
async def ping(ctx):
  embed = discord.Embed(title=":ping_pong: Pong!", description=f"`{round(client.latency * 1000, 1)} ms`", color=0x3983f2)
  await ctx.send(embed=embed)

@client.command()
async def link(ctx):
  if isinstance(ctx.channel, discord.channel.DMChannel):
    await auth_process(ctx.author)
  else:
    embed=discord.Embed(title = "ℹ️ 前往私人訊息以繼續", description = f"為保護你的資料安全，請於私人訊息完成綁定。", color=0x3983f2)
    await ctx.reply(embed=embed, delete_after = 5.0, mention_author=False)
    await auth_process(ctx.author)

@slash.slash(description="綁定推特帳號")
async def link(ctx):
  await ctx.send("Processing...", delete_after = 0.01)
  if isinstance(ctx.channel, discord.channel.DMChannel):
    await auth_process(ctx.author)
  else:
    embed=discord.Embed(title = "ℹ️ 前往私人訊息以繼續", description = f"為保護你的資料安全，請於私人訊息完成綁定。", color=0x3983f2)
    await ctx.channel.send(embed=embed, delete_after = 5.0)
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
    embed=discord.Embed(title = "✅ 註銷成功", description = "已將所有包含使用者授權金鑰的訊息覆蓋，你可以在Twitter的[使用者設定](https://twitter.com/settings/connected_apps)中移除此應用程式的權限。", color=0x3983f2)
    await ctx.send(embed=embed)

@slash.slash(description="解除綁定推特帳號")
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
    embed=discord.Embed(title = "✅ 註銷成功", description = "已將所有包含使用者授權金鑰的訊息覆蓋，你可以在Twitter的[使用者設定](https://twitter.com/settings/connected_apps)中移除此應用程式的權限。", color=0x3983f2)
    await ctx.send(embed=embed)

client.run("OTE3MTIyNDI1MTAyMTYzOTcx.Ya0G0Q.ZgU4NJ3pWFrCoyjNkH8-3M2Ux1Y")