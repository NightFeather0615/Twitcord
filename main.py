import nextcord
from nextcord.ext import commands
import asyncio
import os, sys
import re
import tweepy
import logging
from dotenv import load_dotenv
from typing import Union
import gettext

intents = nextcord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True

client = commands.AutoShardedBot(
  command_prefix = 'tc!',
  intents = intents,
  activity = nextcord.Activity(
    type = nextcord.ActivityType.watching,
    name = "🕊️ | /connect"
  )
)
client.remove_command("help")

logging.basicConfig(
  level = logging.INFO,
  format = '[%(asctime)s] [%(levelname)s] %(message)s',
  datefmt = '%Y/%m/%d %I:%M:%S'
)

I18N_TRANSLATION = {
  "en-US": gettext.translation("en_US", localedir = "./locale", languages = ["en_US"]),
  "zh-TW": gettext.translation("zh_TW", localedir = "./locale", languages = ["zh_TW"]),
  "zh-CN": gettext.translation("zh_CN", localedir = "./locale", languages = ["zh_CN"])
}
I18N_TRANSLATION["en-US"].install()

load_dotenv()
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_POST_URL_REGEX = re.compile(r"https:\/\/(www\.)?(twitter|fxtwitter)\.com\/[A-Za-z0-9_][^ =&/:]{1,15}\/status\/[0-9]{19}")

@client.event
async def on_ready() -> None:
  logging.info(f"Logged in as {client.user}")

@client.event
async def on_error(event: str) -> None:
  error = sys.exc_info()
  logging.error(f"Event {event} raised {error[0].__name__}: {error[1]}")

@client.event
async def on_resumed() -> None:
  logging.info(f"Connection resumed")

@client.event
async def on_connect() -> None:
  logging.info("Connected to Discord")
  await client.sync_all_application_commands()

@client.event
async def on_disconnect() -> None:
  logging.warning("Disconnected to Discord")

@client.application_command_before_invoke
async def application_command_before_invoke(hook: nextcord.Interaction):
  i18n_translate(hook.locale)

def i18n_translate(domain: str) -> None:
  if I18N_TRANSLATION.get(domain) is None:
    I18N_TRANSLATION["en-US"].install()
  else:
    I18N_TRANSLATION[domain].install()

def get_post_id_from_url(content: str) -> Union[str, None]:
  matchs = TWITTER_POST_URL_REGEX.search(content)
  if matchs is None:
    return None
  return matchs.group().split('/')[-1]

async def connect_account(interaction: nextcord.Interaction, isDM: bool = False) -> None:
  try:
    await interaction.user.create_dm()
    pins = await interaction.user.dm_channel.pins()
    if pins is None:
      return None
    for message in pins:
      await message.unpin()
  except:
    return None

  async for msg in interaction.user.history():
    if msg.author == client.user and msg.content.startswith(("Twitter User Access Token", "Twitter User Token")):
      await msg.edit(content = "[Disconnected] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")
    
  auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
  try:
    embed = nextcord.Embed(
      title = _(":link: Connect to Your Twitter Account"),
      description = _("Please go to [Twitter API Authorize](%s), click on \"Authorize app\", then send the verification PIN code here within 60 seconds") % (auth.get_authorization_url()),
      color = 0x3983f2
    )
    if isDM:
      auth_msg: nextcord.WebhookMessage = await interaction.followup.send(embed = embed)
    else:
      auth_msg = await interaction.user.send(embed = embed)
  except:
    return None

  def check(m: nextcord.Message) -> bool:
    return m.author != auth_msg.author and m.channel.id == auth_msg.channel.id and not m.author.bot
  try:
    pin_code_msg: nextcord.Message = await client.wait_for(event = "message", check = check, timeout = 75.0)
  except asyncio.TimeoutError:
    embed = nextcord.Embed(
      title = _(":warning: Connect Failed"),
      description = _("Authorization timeout, please try again"),
      color = 0xeca42c
    )
    embed.set_footer(text = "ERR_TIMEOUT")
    await interaction.user.send(embed = embed)
  else:
    try:
      auth.get_access_token(pin_code_msg.content)
    except:
      embed = nextcord.Embed(
        title = _(":warning: Connect Failed"),
        description = _("Unauthorized PIN code"),
        color = 0xeca42c
      )
      embed.set_footer(text = "ERR_UNAUTHORIZED")
      await interaction.user.send(embed = embed)
    else:
      embed = nextcord.Embed(
        title = _(":white_check_mark: Account Connected"),
        description = _("You can disconnect to your account by using `/disconnect` at any time"),
        color = 0x3983f2
      )
      await interaction.user.send(embed = embed)
      token_msg = await interaction.user.send(f"Twitter User Access Token\n||`{auth.access_token}`||\n||`{auth.access_token_secret}`||")
      await token_msg.pin()

async def disconnect_account(interaction: nextcord.Interaction, isDM: bool = False) -> None:
  try:
    await interaction.user.create_dm()
    pins = await interaction.user.dm_channel.pins()
    if pins is None:
      return None
    for message in pins:
      await message.unpin()
  except:
    return None

  async for msg in interaction.user.history():
    if msg.author == client.user and msg.content.startswith(("Twitter User Access Token", "Twitter User Token")):
      await msg.edit(content = "[Disconnected] Twitter User Access Token\n`[Access Token cancelled]`\n`[Access Token Secret cancelled]`")

  embed = nextcord.Embed(
    title = _(":white_check_mark: Account Disconnected"),
    description = _("All messages containing user access keys have been overwritten\n\nYou can revoke the permissions of this application in Twitter's [user settings](https://twitter.com/settings/connected_apps)"),
    color = 0x3983f2
  )
  if isDM and interaction is not None:
    await interaction.followup.send(embed = embed)
  else:
    await interaction.user.send(embed = embed)

async def get_twitter_client(user: Union[nextcord.User, nextcord.Member], notify: bool) -> Union[tweepy.Client, None]:
  try:
    await user.create_dm()
    pins = await user.dm_channel.pins()
    if pins is None or len(pins) == 0:
      return None
  except:
    return None
  
  if not pins[0].content.startswith("Twitter User Access Token") and notify is True:
    link_notify_embed = nextcord.Embed(
      title = _(":information_source: You Haven't Connected Your Twitter Account Yet"),
      description = _("Use `/connect` to connect to your Twitter account, then you can interact with Twitter in Discord"),
      color = 0x3983f2
    )
    try:
      await user.send(embed = link_notify_embed)
    finally:
      return None
  
  token_list = pins[0].content.split("\n")
  auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
  access_token = token_list[1].replace("`", "").replace("||", "")
  access_token_secret = token_list[2].replace("`", "").replace("||", "")
  auth.set_access_token(access_token, access_token_secret)

  return tweepy.Client(
    bearer_token = TWITTER_BEARER_TOKEN,
    consumer_key = TWITTER_CONSUMER_KEY,
    consumer_secret = TWITTER_CONSUMER_SECRET,
    access_token = access_token,
    access_token_secret = access_token_secret
  )

@client.event
async def on_raw_reaction_add(payload: nextcord.RawReactionActionEvent) -> None:
  channel = client.get_channel(payload.channel_id)
  if channel is None:
    return None

  message = await channel.fetch_message(payload.message_id)
  if TWITTER_POST_URL_REGEX.search(message.content) is None or str(payload.emoji) not in ["❤️", "🔁", "📡"]:
    return None

  user = client.get_user(int(payload.user_id))
  if user.bot:
    return None

  twitter_client = await get_twitter_client(user, False)
  if twitter_client is None:
    return None
    
  match str(payload.emoji):
    case "❤️":
      twitter_client.like(get_post_id_from_url(message.content))

    case "🔁":
      twitter_client.retweet(get_post_id_from_url(message.content))
      
    case "📡":
      tweet = twitter_client.get_tweet(
        get_post_id_from_url(message.content),
        expansions = 'author_id'
      )
      twitter_client.follow_user(tweet.includes['users'][0].id)
          
    # case "📥":
    #   tweet_id = get_post_id_from_url(message.content)
    #   tweet = twitter_client.get_tweet(tweet_id, expansions='attachments.media_keys', media_fields='url')
    #   medias = tweet.includes['media']
    #   await download_image(user, tweet_id ,medias)

@client.event
async def on_raw_reaction_remove(payload: nextcord.RawReactionActionEvent) -> None:
  channel = client.get_channel(payload.channel_id)
  if channel is None:
    return None

  message = await channel.fetch_message(payload.message_id)
  if TWITTER_POST_URL_REGEX.search(message.content) is None or str(payload.emoji) not in ["❤️", "🔁", "📡"]:
    return None

  user = client.get_user(int(payload.user_id))
  if user.bot:
    return None

  twitter_client = await get_twitter_client(user, False)
  if twitter_client is None:
    return None

  match str(payload.emoji):
    case "❤️":
      twitter_client.unlike(get_post_id_from_url(message.content))

    case "🔁":
      twitter_client.unretweet(get_post_id_from_url(message.content))
      
    case "📡":
      tweet = twitter_client.get_tweet(
        get_post_id_from_url(message.content),
        expansions = 'author_id'
      )
      twitter_client.unfollow_user(tweet.includes['users'][0].id)

@client.event
async def on_message(message: nextcord.Message) -> None:
  if TWITTER_POST_URL_REGEX.search(message.content) is None or isinstance(message.channel, nextcord.DMChannel):
    return None
  for emoji in ["📡", "🔁", "❤️"]:
    try:
      await message.add_reaction(emoji)
    finally:
      await asyncio.sleep(0.3)
  await client.process_commands(message)

@client.slash_command(
  name = "invite",
  name_localizations = {
    nextcord.Locale.zh_TW: "邀請連結",
    nextcord.Locale.zh_CN: "邀请连结",
  },
  description = "Show invite link",
  description_localizations = {
    nextcord.Locale.zh_TW: "顯示機器人邀請連結",
    nextcord.Locale.zh_CN: "显示机器人邀请连结",
  }
)
async def slash_invite(interaction: nextcord.Interaction) -> None:
  embed = nextcord.Embed(
    title = "",
    description = _("Click [here](%s) to invite <@!%s> to your server!") % ("https://discord.com/oauth2/authorize?client_id=917122425102163971&permissions=412317248576&scope=bot%20applications.commands", client.user.id),
    color = 0x3983f2
  )
  await interaction.response.send_message(embed = embed, ephemeral = True)

@client.slash_command(
  name = "support",
  name_localizations = {
    nextcord.Locale.zh_TW: "支援",
    nextcord.Locale.zh_CN: "支援",
  },
  description = "Contact developers outside Discord",
  description_localizations = {
    nextcord.Locale.zh_TW: "在 Discord 外與開發者聯絡",
    nextcord.Locale.zh_CN: "在 Discord 外与开发者联络",
  }
)
async def slash_support(interaction: nextcord.Interaction) -> None:
  embed = nextcord.Embed(
    title = "",
    description = "[GitHub Issues](https://github.com/NightFeather0615/Twitcord/issues)",
    color = 0x3983f2
  )
  await interaction.response.send_message(embed = embed, ephemeral = True)

@client.slash_command(
  name = "connect",
  name_localizations = {
    nextcord.Locale.zh_TW: "連接",
    nextcord.Locale.zh_CN: "连接",
  },
  description = "Connect to your Twitter account",
  description_localizations = {
    nextcord.Locale.zh_TW: "連接你的 Twitter 帳號",
    nextcord.Locale.zh_CN: "连接你的 Twitter 帐号",
  }
)
async def slash_connect(interaction: nextcord.Interaction) -> None:
  if isinstance(interaction.channel, nextcord.PartialMessageable):
    await interaction.response.defer()
  else:
    await interaction.response.send_message(
      _("Please check your DM, and make sure you turned allow direct messages on"),
      ephemeral = True
    )
  await connect_account(interaction, isinstance(interaction.channel, nextcord.PartialMessageable))

@client.slash_command(
  name = "disconnect",
  name_localizations = {
    nextcord.Locale.zh_TW: "斷開連接",
    nextcord.Locale.zh_CN: "断开连接",
  },
  description = "Disconnect to your Twitter account",
  description_localizations = {
    nextcord.Locale.zh_TW: "中斷與 Twitter 帳號的連接",
    nextcord.Locale.zh_CN: "中断与 Twitter 帐号的连接",
  }
)
async def slash_disconnect(interaction: nextcord.Interaction) -> None:
  if isinstance(interaction.channel, nextcord.PartialMessageable):
    await interaction.response.defer()
  else:
    await interaction.response.send_message(
      _("Please check your DM, and make sure you turned allow direct messages on"),
      ephemeral = True
    )
  await disconnect_account(interaction, isinstance(interaction.channel, nextcord.PartialMessageable))

if __name__ == "__main__":
  client.run(os.getenv("DISCORD_BOT_TOKEN"))



# ! ~ The code below is archived/discarded ~ ! #

# import matplotlib as mpl
# import matplotlib.pyplot as plt
# from matplotlib import *

# @client.command()
# async def ping(ctx, index=None):
#   if index == None: index = 10
#   try:
#     index = int(index)
#   except:
#     embed=discord.Embed(title = "⚠️ Command Failed", description = "Invalid integer.\n`tc!ping <index(1~60)>`", color=0xeca42c)
#     embed.set_footer(text="ERR_BADARGUMENT")
#     await ctx.send(embed=embed)
#   if type(index) == int:
#     if 0 < index <= 60:
#       msg = await ctx.send("Tracking bot latency...   □□□□□□□□□□ 0.0%")
#       await ping_calc(ctx, msg, index)
#     else:
#       embed=discord.Embed(title = "⚠️ Command Failed", description = "Index out of range(1~60).\n`tc!ping <index(1~60)>`", color=0xeca42c)
#       embed.set_footer(text="ERR_INVALIDVALUE")
#       await ctx.send(embed=embed)

# @slash.slash(description="Track bot latency")
# async def ping(ctx, index:int=10):
#   if 0 < index <= 60:
#     msg = await ctx.send("Tracking bot latency...   □□□□□□□□□□ 0.0%")
#     await ping_calc(ctx, msg, index)
#   else:
#     embed=discord.Embed(title = "⚠️ Command Failed", description = "Index out of range(1~60).\n`/ping <index(1~60)>`", color=0xeca42c)
#     embed.set_footer(text="ERR_INVALIDVALUE")
#     await ctx.send(embed=embed)

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

# async def ping_calc(ctx, msg, index):
#   time_elsp = []
#   ping_rec = []
#   file_id = (str(datetime.datetime.now().timestamp()) + str(ctx.author.id) + str(ctx.channel.id)).replace(".", "")
#   start_time = datetime.datetime.now().strftime('%H:%M:%S')
#   for i in range(1, index+1):
#     loading_dot = "." + "." * int(i % 3) + " " * int(5 - (i % 3))
#     progress = ("■" * round(i/index*10)) + ("□" * (10 - round(i/index*10)))
#     loading_animation = f"Tracking bot latency{loading_dot}{progress} {round(i/index*100, 1)}%"
#     time_elsp.append(datetime.datetime.now().strftime('%H:%M:%S'))
#     before = time.perf_counter()
#     await msg.edit(content = loading_animation)
#     after = time.perf_counter()
#     ping_rec.append(round((after - before) * 1000, 1))
#     await asyncio.sleep(1)
#   end_time = time_elsp[index-1]
#   max_ping = max(ping_rec)
#   min_ping = min(ping_rec)
#   avg_ping = round(sum(ping_rec) / index, 1)
#   fig = plt.figure(figsize=(20, 10), facecolor="#303340")
#   ax = plt.subplot(1,1,1)
#   ax.plot(time_elsp, ping_rec, 'o-', c="#ffffff", markeredgecolor="#ffffff")
#   ax.set_facecolor("#303340")
#   ax.tick_params(axis = "x", colors="#3983f2", rotation=270)
#   ax.tick_params(axis = "y", colors="#3983f2")
#   ax.yaxis.grid(linestyle="--", linewidth = 0.5)
#   ax.set_axisbelow(True)
#   for pos in ['top', 'right', 'bottom', 'left']:
#     ax.spines[pos].set_visible(False)
#   fig = plt.gcf()
#   plt.savefig(f"./catch/{file_id}.png")
#   file = discord.File(f"./catch/{file_id}.png", filename="image.png")
#   await msg.delete()
#   embed = discord.Embed(title=f"📑 Latency record from {start_time} to {end_time}", description=f"Max: {max_ping} ms | Min: {min_ping} ms | Avg: {avg_ping} ms", color=0x3983f2)
#   embed.set_image(url=f"attachment://image.png")
#   embed.set_footer(text=f"Request by {ctx.author.name}#{ctx.author.discriminator}")
#   await ctx.channel.send(embed=embed, file=file)
#   os.remove(f"./catch/{file_id}.png")