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


@client.event
async def on_ready():
  client.uptime = datetime.datetime.utcnow()
  DiscordComponents(client)
  print('<Logged in as {0.user}>'.format(client))

@client.event
async def on_raw_reaction_add(payload):
  message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
  emoji_list = ["❤️", "🔁"]
  if message.content.startswith("https://twitter.com"):
    user = client.get_user(int(payload.member.id))
    if user != client.user:
      pins = await user.pins()
      if len(pins) != 0 and str(payload.emoji) in emoji_list:
        if pins[0].content.startswith("Twitter User Token"):
          token_list = pins[0].content.split("\n")
          auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
          auth.set_access_token(token_list[1].replace("`", ""), token_list[2].replace("`", ""))
          api = tweepy.API(auth)
          twitter_url = message.content
          twitter_url = twitter_url.split("/")[5::3]
          twitter_url = twitter_url[0].split("?")[::]
          twitter_url = twitter_url[0]
          if str(payload.emoji) == "❤️":
            api.create_favorite(twitter_url)
          if str(payload.emoji) == "🔁":
            api.retweet(twitter_url)

@client.event
async def on_message(message):
  if message.content.startswith("https://twitter.com"):
    await message.add_reaction("❤️")
    await message.add_reaction("🔁")
  await client.process_commands(message)

@client.command()
async def setup(ctx):
  if isinstance(ctx.channel, discord.channel.DMChannel):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    await ctx.send(auth.get_authorization_url())
    def check(m):
      return m.author == ctx.author and m.channel == ctx.channel
    try:
      msg = await client.wait_for(event="message", check=check, timeout=60.0)
    except asyncio.TimeoutError:
      embed=discord.Embed(title = "⚠️ 操作失敗", description = "等候逾時，請重新嘗試。", color=0xeca42c)
      embed.set_footer(text="ERR_TIMEOUT")
      await ctx.send(embed=embed)
    else:
      try:
        auth.get_access_token(msg.content)
      except:
        embed=discord.Embed(title = "⚠️ 操作失敗", description = "驗證失敗，憑證遭拒。", color=0xeca42c)
        embed.set_footer(text="ERR_UNAUTHORIZED")
        await ctx.send(embed=embed)
      else:
        await ctx.send("驗證成功，為確保你的資訊安全，本機器人並**不**將你的資料儲存，而是在你進行反應時從私人訊息釘選抓取金鑰，所以請不要隨意釘選/解釘訊息。")
        token_msg = await ctx.send(f"Twitter User Token\n`{auth.access_token}`\n`{auth.access_token_secret}`")
        await token_msg.pin()
  else:
    await ctx.send("為保護你的資料安全，請前往私人訊息以繼續設定。")

client.run("OTE3MTIyNDI1MTAyMTYzOTcx.Ya0G0Q.ZgU4NJ3pWFrCoyjNkH8-3M2Ux1Y")
