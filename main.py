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

client = commands.Bot(command_prefix='tc!', intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name=f"🕊️ | Type tc!setup in DM"))
slash = SlashCommand(client, sync_commands=True)

consumer_key = "QI2PdLu5ewUDlDr41tSsrvzDo"
consumer_secret="EzP5PtU5omjlTAHS71jF20m9KhifyZwbOxGpso5wnQMgV4olSz"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAGZGWgEAAAAAnoGIiO%2B4fAh2BQC0Vc2yGw8uEmA%3DEWgL9g7KNbn5N7eyZd3v4JoZhbwKeFL8wOw3LvrCt8sYcHXkCE"
twitter_url = ["https://twitter.com"]

def get_id_from_url(url):
  url = url.split("https://twitter.com")
  url = url[1].split("/")[3::3]
  url = url[0].split("?")[::]
  url = url[0]
  return url

async def auth_process(channel):
  pins = await channel.pins()
  if len(pins) != 0:
    for message in pins:
      await message.unpin()
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
        embed=discord.Embed(title = "✅ 綁定成功", description = "為確保你的資訊安全，本機器人並**不**將你的資料儲存，而是在你進行反應時從私人訊息釘選抓取金鑰，所以請不要隨意釘選/解釘訊息。\n\n**如因Discord帳號遭盜用導致資料外洩，開發者不負任何責任，請自行承擔損失。**", color=0x3983f2)
        await channel.send(embed=embed)
        token_msg = await channel.send(f"Twitter User Token\n`{auth.access_token}`\n`{auth.access_token_secret}`")
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
  if any(word in message.content for word in twitter_url):
    user = client.get_user(int(payload.member.id))
    if user != client.user:
      pins = await user.pins()
      link_notify_embed=discord.Embed(title = "ℹ️ 你尚未綁定Twitter帳號", description = f"輸入`tc!setup`來綁定Twitter帳號，方可使用Discord反應來喜歡、轉推或追蹤作者。", color=0x3983f2)
      if len(pins) == 0 and str(payload.emoji) in emoji_list:
        try:
          await user.send(embed=link_notify_embed)
        except:
          pass
      if len(pins) == 0 and str(payload.emoji) == "🔗":
        await auth_process(user)
      if len(pins) != 0 and str(payload.emoji) in emoji_list:
        if pins[0].content.startswith("Twitter User Token"):
          token_list = pins[0].content.split("\n")
          auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
          auth.set_access_token(token_list[1].replace("`", ""), token_list[2].replace("`", ""))
          tp_client = tweepy.Client(bearer_token = bearer_token, consumer_key = consumer_key, consumer_secret = consumer_secret, access_token = token_list[1].replace("`", ""), access_token_secret = token_list[2].replace("`", ""))
          if str(payload.emoji) == "❤️":
            try:
              tp_client.like(get_id_from_url(message.content))
            except:
              pass
          if str(payload.emoji) == "🔁":
            try:
              tp_client.retweet(get_id_from_url(message.content))
            except:
              pass
          if str(payload.emoji) == "📡":
            try:
              tweet = tp_client.get_tweet(get_id_from_url(message.content), expansions='author_id')
              tp_client.follow_user(tweet.includes['users'][0].id)
            except:
              pass

@client.event
async def on_message(message):
  if any(word in message.content for word in twitter_url):
    reaction_list = ["🔗", "📡", "🔁", "❤️"]
    for i in reaction_list:
      await message.add_reaction(i)
      await asyncio.sleep(0.3)
  await client.process_commands(message)

@client.command()
async def setup(ctx):
  if isinstance(ctx.channel, discord.channel.DMChannel):
    await auth_process(ctx.author)
  else:
    embed=discord.Embed(title = "ℹ️ 前往私人訊息以繼續", description = f"為保護你的資料安全，請於私人訊息完成綁定。", color=0x3983f2)
    await ctx.send(embed=embed)
    await auth_process(ctx.author)

client.run("OTE3MTIyNDI1MTAyMTYzOTcx.Ya0G0Q.ZgU4NJ3pWFrCoyjNkH8-3M2Ux1Y")
