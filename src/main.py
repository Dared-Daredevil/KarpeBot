from argparse import ArgumentTypeError
import dotenv
import math
import sys
import datetime
import time
import re
import ruamel.yaml as yaml
import pathlib
import json
#import asyncio
import random
#import traceback
#import hashlib
import numexpr
import sympy
#import numpy
#import copy

import atexit

import discord.client
import discord.abc
import discord.types.activity
from discord.ext import commands

from colorama import Fore, Back, Style

from version import *

from utils import *

from exception import AuthenticationException

import sqlite3

save: dict = {}

yml = yaml.YAML()

VERSION = Version(major=2, minor=2, patch=1)
LOG = False
COINNAME = "Karpcoins"
MAINTANANCE = False

#database = sqlite3.connect("save.sqlite", 10)

autoResponses = {}

async def addCoins(member, amount):
    if not 'users' in save:
        save['users'] = {}
    if not member.id in save['users']:
        save['users'][member.id] = {}
    if not 'coins' in save['users'][member.id]:
        save['users'][member.id]['coins'] = 0
    save['users'][member.id]["coins"] += amount

    # Save it
    saveData()

def saveData():
    global save
    with open('save.yaml', 'w') as outfile:
        yml.dump(save, outfile)

def loadData():
    global save
    with open('save.yaml', 'r') as infile:
        save = yaml.safe_load(infile)

loadData()
saveData()

def getPrefix(bot: commands.Bot, message: discord.Message):
    if not save['guilds']:
        save['guilds'] = {}
    if message.guild:
        if message.guild.id in save['guilds']:
            if 'prefix' in save['guilds'][message.guild.id]:
                return save['guilds'][message.guild.id]['prefix']
    else:
        if 0 in save['guilds']:
            if 'prefix' in save['guilds'][0]:
                return save['guilds'][0]['prefix']
    return "$"

# Open file save.yaml and load it into the save variable
try:
    loadData()
except FileNotFoundError:
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Could not find save.yaml. Creating it now.")
    with open('save.yaml', 'w') as f:
        yaml.dump(save, f)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=(getPrefix), intents=intents, owner_ids=[941433256010727484])

@bot.command(
    aliases=["getping"],help="""
Tells you the ping of the bot
Usage:
 - `ping`
""" 
)
async def ping(ctx: commands.Context):
    embed = discord.Embed(title="Pong!", description=f"{ctx.bot.latency * 1000:.0f}ms", color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command(aliases=["version"], help="""
Gets the bots about page
Usage:
 - `about`
""" )
async def about(ctx: commands.Context):
    embed = discord.Embed(title = f"About KarpeBot", description = f"""
**KarpeBot version {VERSION}**
OS: {getOSVersion()}
Python: {getPythonVersion()}
Pycord: {getDiscordVersion()}
Repository: <https://github.com/LmaxplayG/Karpebot>
    """,
    color = discord.Colour(0x0088FF)
    )
    embed.set_footer(text = "Requested by " + ctx.author.name, icon_url = ctx.author.avatar.url)
    
    #embed.set_image(url=f"{bot.user.display_avatar.url}?size=64")
    
    await ctx.send( embed=embed )

@bot.command(aliases=["codeformat"], help="""
Tells you how to format code
Usage:
 - `format`
""",
 )
async def format(ctx: commands.Context):
    embed = discord.Embed(title = f"How to format code", description = """
Use
\\`\\`\\`
<code>
\\`\\`\\`
to create a codeblock
this will result in
```
print("Hello world!") # This is an example
```
add syntax highlighting by replacing <language> with for example, for python:
`python`
```python
print("Hello world!")
```
this was achieved by typing
\\`\\`\\`python
print("Hello world!")
\\`\\`\\`
    """,
    color = discord.Colour(0x0088FF)
    )

    embed.set_footer(text = "Requested by " + ctx.author.name, icon_url = ctx.author.avatar.url)
    
    await ctx.send( embed=embed )

@bot.command( aliases=[], help="""
Kicks the specified user
Usage:
    - `kick @user <reason>`
""")
async def kick(ctx: commands.Context, member: commands.MemberConverter, *, reason: str = "No reason specified"):
    #if member is invalid, return and give an error
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if ctx.author.top_role.position <= member.top_role.position:
        await ctx.send("You cannot kick this user")
        return

    #prevent the bot from kicking itself
    if member.id == bot.user.id:
        await ctx.send("I cannot kick myself")
        return

    if not ctx.author.guild_permissions.kick_members:
        return

    if not member.bot:
        embed = discord.Embed(title = f"You have been kicked from {ctx.guild.name}", description = "Reason:```\n{reason}```", color = discord.Colour(0x0088FF))
        await member.send(embed=embed)

    await member.kick(reason=reason)

    embed = discord.Embed(title = f"{member.name} has been kicked", description = """
User {0} has been kicked
Reason:
```
{1}
```
""".format(
    member.mention,
    reason
    ), color=discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

@bot.command( aliases=[], help="""
Bans the specified user
Usage:
    - `ban @user <reason>`
    - `ban <user id> <reason>`
""")
async def ban(ctx: commands.Context, member: commands.MemberConverter = None, *, reason: str = "No reason specified"):
    member: discord.member = member
    #if member is invalid, return and give an error
    if not member:
        embed = discord.Embed(title = f"Invalid user", description = "Please specify a valid user", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return
    if member.guild != ctx.guild:
        return
    
    # If user is not a mod or higher, return
    if not ctx.author.guild_permissions.ban_members:
        embed = discord.Embed(title = f"You do not have permission to ban this user", description = "You must be a mod or higher to ban this user\nOr have the permission to ban members", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return

    # do we have a higher role than the user?
    if ctx.author.top_role.position <= member.top_role.position:
        embed = discord.Embed(title = f"You do not have permission to ban this user", description = "You need to have a higher role than the user to ban them", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return

    #prevent the bot from banning itself
    if member.id == bot.user.id:
        await ctx.send("I cannot ban myself")
        return

    if not member.bot:
        embed = discord.Embed(title = f"You have been banned from {ctx.guild.name}", description = "Reason:```\n{reason}```", color = discord.Colour(0x0088FF))
        await member.send(embed=embed)

    await member.ban(reason=reason)
    
    embed = discord.Embed(title = f"{member.name} has been banned", description = """
User {0} has been banned
Reason:
```
{1}
```
""".format(
    member.mention,
    reason
    ), color=discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

# Klck command (fake kick)

@bot.command( aliases=['k¡ck'], help="""
Kicks the specified user
Usage:
    - `klck @user <reason>`
""")
async def klck(ctx: commands.Context, member: commands.MemberConverter, *, reason: str = "No reason specified"):
    #if member is invalid, return and give an error
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if ctx.author.top_role.position <= member.top_role.position:
        await ctx.send("You cannot kick this user")
        return

    #prevent the bot from kicking itself
    if member.id == bot.user.id:
        await ctx.send("I cannot kick myself")
        return

    if not ctx.author.guild_permissions.kick_members:
        return

    if not member.bot:
        embed = discord.Embed(title = f"You have been kicked from {ctx.guild.name}", description = "Reason:```\n{reason}```", color = discord.Colour(0x0088FF))
        await member.send(embed=embed)

    embed = discord.Embed(title = f"{member.name} has been kicked", description = """
User {0} has been kicked
Reason:
```
{1}
```
""".format(
    member.mention,
    reason
    ), color=discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

@bot.command( aliases=[], help="""
Bans the specified user
Usage:
    - `bon @user <reason>`
    - `bon <user id> <reason>`
""")
async def bon(ctx: commands.Context, member: commands.MemberConverter = None, *, reason: str = "No reason specified"):
    member: discord.member = member
    #if member is invalid, return and give an error
    if not member:
        embed = discord.Embed(title = f"Invalid user", description = "Please specify a valid user", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return
    if member.guild != ctx.guild:
        return
    
    # If user is not a mod or higher, return
    if not ctx.author.guild_permissions.ban_members:
        embed = discord.Embed(title = f"You do not have permission to ban this user", description = "You must be a mod or higher to ban this user\nOr have the permission to ban members", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return

    # do we have a higher role than the user?
    if ctx.author.top_role.position <= member.top_role.position:
        embed = discord.Embed(title = f"You do not have permission to ban this user", description = "You need to have a higher role than the user to ban them", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return

    #prevent the bot from banning itself
    if member.id == bot.user.id:
        await ctx.send("I cannot ban myself")
        return

    if not member.bot:
        embed = discord.Embed(title = f"You have been banned from {ctx.guild.name}", description = "Reason:```\n{reason}```", color = discord.Colour(0x0088FF))
        await member.send(embed=embed)
    
    embed = discord.Embed(title = f"{member.name} has been banned", description = """
User {0} has been banned
Reason:
```
{1}
```
""".format(
        member.mention,
        reason
    ), color=discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

@bot.command( aliases=[], help="""
Bans the specified user
Usage:
    - `unban @user`
    - `unban <user id>`
""")
async def unban(ctx: commands.Context, member: commands.MemberConverter, *, reason: str = "No reason specified"):
    #if member is invalid, return and give an error
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    # do we have a higher role than the user?
    if ctx.author.top_role.position <= member.top_role.position:
        await ctx.send("You cannot ban this user")
        return

    #prevent the bot from banning itself
    if member.id == bot.user.id:
        await ctx.send("I cannot ban myself")
        return

    if not ctx.author.guild_permissions.ban_members:
        return

    await member.unban(reason=reason)
    
    embed = discord.Embed(title = f"{member.name} has been unbanned", description = """
User {0} has been banned
Reason:
```
{1}
```
""".format(
    member.mention,
    reason
    ), color=discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

#Command that deletes all messages in the specified channel
@bot.command(aliases=[], help="""
Deletes all messages in the specified channel
Usage:
    - `purge <amount>`
    - `purge <amount> <channel>`
    - `purge <amount> <channel> <user>`
""")
async def purge(ctx: commands.Context, amount: int, channel: discord.TextChannel = None, user: commands.MemberConverter = None):
    if not channel:
        channel = ctx.channel
    
    if amount > 1000:
        await ctx.send("You cannot delete more than 1000 messages")
        return
    if amount < 1:
        await ctx.send("You cannot delete less than 1 message")
        return
    if not ctx.author.guild_permissions.manage_messages:
        return

    deleted = 0
    if user == None:
        await ctx.channel.purge(limit=amount, oldest_first=False)
        deleted = amount
    else:
        async for message in channel.history(limit=amount):
            if message.author == user:
                await message.delete()
                deleted += 1
    await ctx.send(f"Deleted {deleted} messages", delete_after=5)

# Command to get the bot's uptime
@bot.command(aliases=[], help="""
Gets the bots uptime
Usage:
    - `uptime`
""")
async def uptime(ctx: commands.Context):
    currentTime = time.time()
    difference = currentTime - startTime

    # Change differences precision to seconds
    difference = round(difference, 0)

    # Format difference to a readable string in python 3
    difference = str(datetime.timedelta(seconds=difference))

    await ctx.send(f"Uptime: {difference}")

# Command to get server rules
@bot.command(aliases=[], help="""
Gets the server's rules
Usage:
    - `rules`
""")
async def rules(ctx: commands.Context):
    ruleschannel = ctx.guild.rules_channel
    # Get oldest message in rules channel
    message = await ruleschannel.history(limit=1, oldest_first=True).flatten()
    rules = message[0].content.replace("@everyone", "")
    # Create a new embed with the rules
    embed = discord.Embed(title = f"{ctx.guild.name}'s rules", description = rules, color = discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

# Thanks command
@bot.command(aliases=[], help="""
Thanks the specified user
Usage:
    - `thanks @user`
    - `thanks <user id>`
""")
async def thanks(ctx: commands.Context, member: commands.MemberConverter):
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if member.id == bot.user.id:
        await ctx.send("I cannot thank myself")
        return
    if member.id == ctx.author.id:
        await ctx.send("You cannot thank yourself")
        return
    #if ctx.author.top_role.position <= member.top_role.position:
    #    await ctx.send("You cannot thank this user")
    #    return
    if not ctx.author.guild_permissions.manage_messages:
        return
    embed = discord.Embed(title = f"{ctx.author.name} has thanked {member.name}", description = "", color = discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

@bot.command(aliases=[], help="""
Sends a message to all members of the server that it was sent in
Usage:
    - `botsend <message>`
""")
async def botsend(ctx: commands.Context, *, message: str):
    # check if the user is the owner of the bot, if it isn't, return
    if not ctx.author.id in bot.owner_ids:
        return
    embed = discord.Embed(title = f"Message from {ctx.guild.name}", description = message, color = discord.Colour(0x0088FF))
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    embed.set_footer(text=f"If this is being spammed, please leave the server this message originated from or contact the bot owner (<@{bot.owner_ids[0]}>)")
    for member in ctx.guild.members:
        try:
            await member.send(embed=embed)
        except:
            pass

# Karpe command
@bot.command(aliases=[], help="""
Karpe the specified user
Usage:
    - `karpe @user`
    - `karpe <user id>`
""")
async def karpe(ctx: commands.Context, member: commands.MemberConverter):
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if member.id == bot.user.id:
        await ctx.send("I cannot karpe myself")
        return
    name = member.name
    if member.nick:
        name = member.nick

    name = re.escape(name)
    name = name.replace("\\ ", " ")
    name = name.replace("_", r"\_")
    await ctx.send(f"{name} has been karpe")

@bot.command(aliases=['addcash', 'addmoney'], help="""
Adds coins to the specified user
Usage:
    - `addcoins @user <amount>`
    - `addcoins <user id> <amount>`
""")
async def addcoins(ctx: commands.Context, member: commands.MemberConverter, amount: float):
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if not member.id:
        await ctx.send("Invalid user")
        return
    if member.id == bot.user.id:
        await ctx.send("I cannot add coins to myself")
        return
    # Only bot owners can change coins
    if not ctx.author.id in bot.owner_ids:
        await ctx.send("You do not have the permission `BOT.OWNER`")
        return

    await addCoins(member, amount)
    await ctx.send(f"Added {amount} {COINNAME} to {member.name}\nThey now have {save['users'][member.id]['coins']} {COINNAME}")

# Command to remove coins from a user
@bot.command(aliases=['removecash', 'removemoney'], help="""
Removes coins from the specified user
Usage:
    - `removecoins @user <amount>`
    - `removecoins <user id> <amount>`
""")
async def removecoins(ctx: commands.Context, member: commands.MemberConverter, amount: float):
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if not member.id:
        await ctx.send("Invalid user")
        return
    if member.id == bot.user.id:
        await ctx.send("I cannot remove coins from myself")
        return
    # Only bot owners can change coins
    if not ctx.author.id in bot.owner_ids:
        await ctx.send("You do not have the permission `BOT.OWNER`")
        return

    await addCoins(member, -amount)
    await ctx.send(f"Removed {amount} {COINNAME} from {member.name}\nThey now have {save['users'][member.id]['coins']} {COINNAME}")

# Command to set the amount of coins a user has
@bot.command(aliases=['setcash', 'setmoney'], help="""
Sets the amount of coins a user has
Usage:
    - `setcoins @user <amount>`
    - `setcoins <user id> <amount>`
""")
async def setcoins(ctx: commands.Context, member: commands.MemberConverter, amount: float):
    if not member:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if not member.id:
        await ctx.send("Invalid user")
        return
    if member.id == bot.user.id:
        await ctx.send("I cannot set coins for myself")
        return
    # Only bot owners can change coins
    if not ctx.author.id in bot.owner_ids:
        await ctx.send("You do not have the permission `BOT.OWNER`")
        return

    # Check if save['users'][member.id] exists
    if not member.id in save['users']:
        save['users'][member.id] = {}
        save['users'][member.id]['coins'] = 0
    if not 'coins' in save['users'][member.id]:
        save['users'][member.id]['coins'] = 0
    save['users'][member.id]['coins'] = amount
    await addCoins(member, 0)
    await ctx.send(f"Set {member.name}'s coins to {amount}")

@bot.command(aliases=[], help="""
Adds coins to the specified user
Usage:
    - `addcoins @user <amount>`
    - `addcoins <user id> <amount>`
""")
async def addcoinsall(ctx: commands.Context, amount: float):
    if not ctx.author.id in bot.owner_ids:
        await ctx.send("You do not have the permission `BOT.OWNER`")
        return

    items: set = set()
    for guild in bot.guilds:
        async for member in guild.fetch_members():
            if not member.bot:
                items.add(member)
    for item in items:
        await addCoins(item, amount)

# Balance command
@bot.command(aliases=['bal'], help="""
Gets the balance of the specified user
Usage:
    - `balance @user`
    - `balance <user id>`
""")
async def balance(ctx: commands.Context, member: commands.MemberConverter = None):
    if not member:
        member = ctx.author
    if not member.id:
        await ctx.send("Invalid user")
        return
    if member.guild != ctx.guild:
        return
    if member.id == bot.user.id:
        await ctx.send("I cannot get the balance of myself")
        return

    # Check if the user data exists
    if not member.id in save['users']:
        save['users'][member.id] = {}
        save['users'][member.id]['coins'] = 0
    
    if not 'coins' in save['users'][member.id]:
        save['users'][member.id]['coins'] = 0
    coins = save['users'][member.id]['coins']
    await ctx.send(f"{member.name} has {coins} {COINNAME}")

# Daily command
@bot.command(aliases=[], help="""
Gives you your daily coins
Usage:
    - `daily`
""")
async def daily(ctx: commands.Context):
    if not save['config']:
        save['config'] = {}
    if not save['config']['daily']:
        save['config']['daily'] = {}
    if not save['config']['daily']['min']:
        save['config']['daily']['min'] = 90
    if not save['config']['daily']['max']:
        save['config']['daily']['min'] = 100
    dailyMin = save['config']['daily']['min']
    dailyMax = save['config']['daily']['max']
    daily_coins = random.randint(90, 100)
    if not ctx.author.id in save['users']:
        save['users'][ctx.author.id] = {}
        save['users'][ctx.author.id]['coins'] = 0
    if not 'daily' in save['users'][ctx.author.id]:
        save['users'][ctx.author.id]['daily'] = 0
    # Check if the user has already claimed their daily today (compare the current day)
    if save['users'][ctx.author.id]['daily'] <= (time.time() - 86400):
        await addCoins(ctx.author, daily_coins)
        embed = discord.Embed(title = f"Daily coins", description = f"You have received {daily_coins} {COINNAME}", color = discord.Colour(0x0088FF))
        embed.set_footer(text=f"You can claim your daily coins again in 24 hours")
        await ctx.send(embed=embed)
        save['users'][ctx.author.id]['daily'] = time.time()
    else:
        embed = discord.Embed(title = f"Daily coins", description = f"You have already claimed your daily coins today", color = discord.Colour(0x0088FF))
        # Format the time left
        time_left = 86400 - (time.time() - save['users'][ctx.author.id]['daily'])
        hours = int(time_left / 3600)
        minutes = int((time_left % 3600) / 60)
        seconds = int(time_left % 60)
        timeString = datetime.time(hours, minutes, seconds).strftime("%H:%M:%S")

        embed.set_footer(text=f"You can claim your daily coins again in {timeString}")
        await ctx.send(embed=embed)
    saveData()

# Coinflip command
@bot.command(aliases=['cf'], help="""
Flips a coin and gives you either heads or tails
Usage:
    - `coinflip`
""")
async def coinflip(ctx: commands.Context):
    # Get a random number between 0 and 1
    coin = random.randint(0, 1)
    if coin <= 0.5:
        await ctx.send("Heads")
    else:
        await ctx.send("Tails")

# Cashflip command
@bot.command(aliases=['moneyflip'], help="""
Flips a coin and gives you either heads or tails
You can bet on heads or tails
Usage:
    - `cashflip <amount> <heads/tails>`
""")
async def cashflip(ctx: commands.Context, amount: float, bet: str):
    # Check if the bet is heads or tails
    if not bet.lower() in ['heads', 'tails']:
        await ctx.send("Invalid bet")
        return
    bet = bet.lower()
    # Generate a random number between 0 and 1
    coin = random.randint(0, 1)

    # Check if the user has enough coins
    if not ctx.author.id in save['users']:
        save['users'][ctx.author.id] = {}
        save['users'][ctx.author.id]['coins'] = 0
    if not 'coins' in save['users'][ctx.author.id]:
        save['users'][ctx.author.id]['coins'] = 0
    if save['users'][ctx.author.id]['coins'] < amount:
        embed=discord.Embed(title="Cashflip", description=f"You don't have enough coins to bet {amount} {COINNAME}", color=discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    
    if amount <= 0:
        embed=discord.Embed(title="Cashflip", description="You must bet more than 0 coins", color=discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    
    # Is amount infinite or nan?
    if math.isnan(amount) or math.isinf(amount):
        embed=discord.Embed(title="Cashflip", description="You must bet more than 0 coins", color=discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return

    if coin <= 0.5:
        coin = 1
    else:
        coin = 0
    # Check if the user has enough coins
    if not ctx.author.id in save['users']:
        save['users'][ctx.author.id] = {}
        save['users'][ctx.author.id]['coins'] = 0
    if not 'coins' in save['users'][ctx.author.id]:
        save['users'][ctx.author.id]['coins'] = 0

    coinStr = "Heads"
    if coin >= 0.5:
        coinStr = "Tails"
    embed = discord.Embed(title = f"Cashflip: {coinStr}", description = f"You have flipped a coin and got {coinStr}", color = discord.Colour(0x0088FF))

    # Check if the user won or lost
    if coin <= 0.5 and bet == "heads":
        await addCoins(ctx.author, amount * 0.75)
        embed.description = f"You won {amount * 0.75} {COINNAME}"
        embed.set_footer(text=f"A 25% fee has been taken from your winnings")
    elif coin >= 0.5 and bet == "tails":
        await addCoins(ctx.author, amount * 0.75)
        embed.set_footer(text=f"A 25% fee has been taken from your winnings")
        embed.description = f"You won {amount * 0.75} {COINNAME}"
    else:
        await addCoins(ctx.author, -amount)
        embed.description = f"You lost {amount} {COINNAME}"
    await ctx.send(embed=embed)

# Pay command
@bot.command(aliases=[], help="""
Pay someone
Usage:
    - `pay <user> <amount>`
""")
async def pay(ctx: commands.Context, user: discord.Member, amount: float):
    
    originalAmount = amount

    if not save['config']:
        save['config'] = {}
    if not 'bank' in save['config']:
        save['config']['bank'] = {}
    if not 'tax' in save['config']['bank']:
        save['config']['bank']['tax'] = {}
    if not 'payment' in save['config']['bank']['tax']:
        save['config']['bank']['tax']['payment'] = 0
    tax = save['config']['bank']['tax']['payment']

    if tax < 0:
        tax = 0
    
    # Round tax to 2 decimal places
    tax = round(tax, 2)

    # Tax the transaction
    amount = amount * (100 + tax) / 100
    # Check if the user has enough coins
    if not ctx.author.id in save['users']:
        save['users'][ctx.author.id] = {}
        save['users'][ctx.author.id]['coins'] = 0
    if not 'coins' in save['users'][ctx.author.id]:
        save['users'][ctx.author.id]['coins'] = 0
    if save['users'][ctx.author.id]['coins'] < amount:
        embed=discord.Embed(title="Pay", description=f"You don't have enough coins to pay {amount} {COINNAME}", color=discord.Colour(0x0088FF))
        embed.set_footer(text=f"You have {save['users'][ctx.author.id]['coins']} {COINNAME}, {tax}% tax has been taken")
        await ctx.send(embed=embed)
        return
    
    if amount <= 0.1:
        embed=discord.Embed(title="Pay", description="You must pay more than 0.1 coins", color=discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    
    # Is amount infinite or nan?
    if math.isnan(amount) or math.isinf(amount):
        embed=discord.Embed(title="Pay", description="You must pay more than 0 coins", color=discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    
    # Pay the user
    await addCoins(ctx.author, -originalAmount)
    await addCoins(user, originalAmount)
    taxed = amount - originalAmount
    # Round taxed to 2 decimal places
    taxed = round(taxed, 3)
    embed=discord.Embed(title="Payment succesfull", description=f"You have paid {user.name} {originalAmount} {COINNAME}\n({taxed} {COINNAME} have been taxed)", color=discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

# Leaderboard command
@bot.command(aliases=['baltop', 'top'], help="""
Gets the top 10 users with the most coins
Usage:
    - `leaderboard`
""")
async def leaderboard(ctx: commands.Context):
    loadingEmbed = discord.Embed(title = "Loading...", color = discord.Colour(0x0088FF), description = "Please wait whilst the leaderboard is being loaded")
    loadingMessage = await ctx.send(embed=loadingEmbed)
    # Get the top 10 users
    users = save['users']
    # Turn the users object into a list
    users = list(users.items())
    # Sort the list by the coins

    errors = 0

    def sort_by_coins(user):
        try:
            # Check if the user data exists
            if not int(user[0]) in save['users']:
                save['users'][int(user[0])] = {}
                save['users'][int(user[0])]['coins'] = 0
            if not 'coins' in save['users'][int(user[0])]:
                save['users'][int(user[0])]['coins'] = 0
            return user[1]['coins']
        except:
            nonlocal errors
            print(f"Error: {user}")
            errors += 1
            return 0

    users.sort(key=sort_by_coins, reverse=True)


    embed = discord.Embed(title = f"Leaderboard (Top {min(10, users.__len__())} / {users.__len__()})", color = discord.Colour(0x0088FF))
    # Add the top 10 users
    for i, user in enumerate(users):
        try:
            # Make the memberName variable
            # Try getting the member name from every guild the bot is in
            if i >= 10:
                break
            memberName = None
            gotName = False
            for guild in bot.guilds:
                try:
                    memberName = guild.get_member(int(user[0])).name + "#" + guild.get_member(int(user[0])).discriminator
                except:
                    pass
            memberNameGuild = ctx.guild.get_member(int(user[0]))
            if memberNameGuild:
                if int(user[0]) == ctx.guild.owner_id:
                    memberName = "`[Server Owner]` " + memberNameGuild.name + "#" + memberNameGuild.discriminator
                else:
                    memberName = "`[Server]` " + memberNameGuild.name + "#" + memberNameGuild.discriminator
                if memberNameGuild.nick:
                    # Append the name to the member name
                    memberName = memberName + " (" + memberNameGuild.nick + ")"
            if not memberName:
                memberName = int(user[0])
            if int(user[0]) in bot.owner_ids:
                memberName = "`[Bot Owner]` " + memberName
            
            if not save['config']:
                save['config'] = {}

            if 'ranks' in save:
                for rank in save['ranks']:
                    if int(user[0]) in save['ranks'][rank]:
                        memberName = f"`[{rank}]` {memberName}"
                        break
            if memberName == None:
                memberName = "Unknown"
            memberName = memberName.__str__().replace('_', '\\_')
            coins: float = user[1]['coins']
            coinsStr = coins.__str__().replace("inf", "Infinity")
            embed.add_field(name = f"{i + 1}. {memberName}", value=f"{coinsStr} {COINNAME}", inline = False)
        except:
            pass
    await ctx.send(embed=embed)
    await loadingMessage.delete()

# Server info command
@bot.command(aliases=['server'], help="""
Gets the server info
Usage:
    - `serverinfo`
""")
async def serverinfo(ctx: commands.Context):
    # Get the guild
    guild = ctx.guild

    embed = discord.Embed(title = f"Server info for {guild.name}", color = discord.Colour(0x0088FF))
    embed.add_field(name = "Server ID", value = guild.id, inline = False)
    embed.add_field(name = "Server owner", value = f"{guild.owner.name}#{guild.owner.discriminator}", inline = False)
    embed.add_field(name = "Server created at", value = guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline = False)
    embed.add_field(name = "Server member count", value = guild.member_count, inline = False)
    embed.add_field(name = "Server verification level", value = guild.verification_level, inline = False)

    embed.set_image(url=guild.icon)

    await ctx.send(embed=embed)

# Slowmode command
@bot.command(aliases=['sm'], help="""
Sets the slowmode for the server
Usage:
    - `slowmode <seconds>`
""")
async def slowmode(ctx: commands.Context, seconds: int):
    # Check if the user has the permission to use this command
    if not ctx.author.guild_permissions.manage_messages:
        embed = discord.Embed(title = "Slowmode", description = "You do not have the permission to use this command", color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    # Check if the user has the permission to use this command
    if not ctx.author.guild_permissions.manage_channels:
        embed = discord.Embed(title = "Slowmode", description = "You do not have the permission to use this command", color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    
    # Check if the input is valid
    if seconds < 0 or seconds > 21600:
        embed = discord.Embed(title = "Invalid delay", description = "The delay should be between 0 and 21600", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return

    # Set the slowmode
    await ctx.channel.edit(slowmode_delay=seconds)

    # Create the embed
    embed = discord.Embed(title = "Slowmode", description = f"The slowmode has been set to {seconds} seconds", color = discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

# Raid command
@bot.command(aliases=[], help="""
Raid a hub (announces it)
Usage:
    - `raid <hub> <time>`
""")
async def raid(ctx: commands.Context, hub: str, intime: int = 3600):
    # Check if the user has the permission to use this command
    if not ctx.author.guild_permissions.manage_messages:
        embed = discord.Embed(title = "Raid", description = "You do not have the permission to use this command", color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    # Check if the user has the permission to use this command
    if not ctx.author.guild_permissions.manage_channels:
        embed = discord.Embed(title = "Raid", description = "You do not have the permission to use this command", color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return

    # Creates an event lasting for the given time
    event = ctx.guild.create_scheduled_event(end_time=datetime.time().fold + intime, name = f"Raid {hub}", start_time=datetime.time(), entity_type=discord.ScheduledEventEntityType.external, description=f"Raiding {hub}")

    # Create the embed
    # IntimeStr is the time in the format of "HH:MM"
    intimeStr = str(datetime.timedelta(seconds=intime))
    embed = discord.Embed(title = "RAID", description = f"{hub.capitalize()} is being raided for {intimeStr}!", color = discord.Colour(0x0088FF))
    await ctx.send("<@&976488038786035772>", embed=embed)
    await ctx.message.delete()

# Command to calculate math expressions
@bot.command(help="""
Calculates math expressions using the python package `numexpr`.
Usage:
    - `numexpr <expression>`
""")
async def numexpr(ctx: commands.Context, *, expression: str):
    # Check if the user has the permission to use this command
    if not ctx.author.id in bot.owner_ids:
        embed = discord.Embed(title = "Numexpr error", description = "You do not have the permission to use this command", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return
    
    # Calculate the expression
    try:
        result = numexpr.evaluate(expression).item()
    except Exception as e:
        embed = discord.Embed(title = "Numexpr Error", description = f"The expression could not be calculated: {e}", color = discord.Colour(0xFF0000))
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title = "Calc", description = f"The result is: {result}", color = discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

# Solve command
@bot.command(aliases=[], help="""
Solves an equation for variables
Usage:
    - `solve <equation>`
""")
async def solve(ctx: commands.Context, *, equation: str):
    # Only bot owners may use it for now as it may cause code injection
    if not ctx.author.id in bot.owner_ids:
        embed = discord.Embed(title = "Solve", description = "You do not have the permission to use this command", color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return

    # If the equation is inside a code block, remove it
    if equation.startswith("```") and equation.endswith("```"):
        equation = equation[3:-3]
    # If its inside single quotes, remove them
    elif equation.startswith("'") and equation.endswith("'"):
        equation = equation[1:-1]

    # Remove any trailing whitespace/newlines
    # equation = equation.strip()

    result = sympy.solve(equation)

    # Create the embed
    embed = discord.Embed(title = "Solve", description = f"The result is:\n```\n{result}```", color = discord.Colour(0x0088FF))
    await ctx.send(embed=embed)

bot.remove_command("help") # Remove default help command

@bot.command( help="""
Gives help about commands,
Usage:
 - `help command <commandname>` - Shows the help for a specific command
 - `help list` - Shows a list of all commands
 - `help search <searchterm>` - Searches for commands
 - `help query <query>` - Searches for commands
""" )
async def help(ctx: commands.Context, command: str = "", arg1: str = ""):
    if command == "" or command.lower() == "help":
        # Get own description
        description = bot.get_command("help").description
        embed = discord.Embed(title = "Help subcommands:", description = """
 - `help` - Shows this message
 - `help command <commandname>` - Shows the help for a specific command
 - `help list` - Shows a list of all commands
 - `help search <searchterm>` - Searches for commands
 - `help query <query>` - Searches for commands
        """, color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return
    if command.lower() == "list":
        helpstr = ""
        # Sort the commands alphabetically
        commands = sorted(bot.commands, key=lambda x: x.name)
        for command in commands:
            if command.name == "help":
                continue
            if len(command.aliases) != 0:
                helpstr += f" - **{command.name} ({' | '.join(command.aliases)})**\n"
            else:
                helpstr += f" - **{command.name}**\n"
        embed = discord.Embed(
            title = "Commands:",
            description = helpstr,
            color = discord.Colour(0x0088FF)
        )
        await ctx.send(embed=embed)
    elif command.lower() == "command":
        helpcommand = None
        for command in bot.commands:
            if command.hidden:
                continue
            if command.name == arg1:
                helpcommand = command
            else:
                for alias in command.aliases:
                    if alias == arg1:
                        helpcommand = command
        
        if helpcommand != None:
            embed = discord.Embed(
                title = f"Command {helpcommand.name}:",
                description = helpcommand.help,
                color = discord.Colour(0x0088FF)
            )

            embed.set_footer(text=helpcommand.hidden)

            print(helpcommand.module)
            if embed.description == "None":
                embed.description = "This command has no help description"
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title = f"Help - Command not found",
                description = "This command doesn't exist, or you might have misspelled it",
                color = discord.Colour(0x0088FF)
            )
            await ctx.send(embed=embed)
    elif command.lower() == "search" or command.lower() == "query":
        # Search for a command, searching if it occurs in the name or in the aliases
        searchstr = arg1.lower()
        commands = sorted(bot.commands, key=lambda x: x.name)
        foundcommands = []
        for command in commands:
            name: str = command.name.lower()
            aliases: list = command.aliases
            if name.find(searchstr) != -1:
                foundcommands.append(command)
            for alias in aliases:
                if alias.find(searchstr) != -1:
                    foundcommands.append(command)
        
        if len(foundcommands) == 0:
            embed = discord.Embed(
                title = "Help - Search",
                description = "No commands with this query were found",
                color = discord.Colour(0x0088FF)
            )
            await ctx.send(embed=embed)
        else:
            # Remove duplicates
            foundcommands = list(dict.fromkeys(foundcommands))
            embed = discord.Embed(
                title = "Help - Search results",
                description = " - " + "\n - ".join([f"**{command.name} ({' | '.join(command.aliases)})**" for command in foundcommands]).replace(" ()", ""),
                color = discord.Colour(0x0088FF)
            )
            await ctx.send(embed=embed)

    else:
        embed = discord.Embed(
            title = f"Help - Command not found",
            description = "This subcommand doesn't exist, or you might have misspelled it",
            color = discord.Colour(0x0088FF)
        )
        await ctx.send(embed=embed)

# Print command (prints the message to the console)
@bot.command(aliases=["print"], help="""
Prints the message to the console
Usage:
    - `print <message>`
""")
async def printmsg(ctx: commands.Context, *, message: str):
    # Only bot owners may use it
    if not ctx.author.id in bot.owner_ids:
        embed = discord.Embed(title = "Print", description = "You do not have the permission to use this command", color = discord.Colour(0x0088FF))
        await ctx.send(embed=embed)
        return

    # If the message is inside a code block, remove it
    if message.startswith("```") and message.endswith("```"):
        message = message[3:-3]
    # If its inside single quotes, remove them
    elif message.startswith("'") and message.endswith("'"):
        message = message[1:-1]

    # Remove any trailing whitespace/newlines
    # message = message.strip()

    print(message)

@bot.command(aliases=["del"], help="""
Deletes the message with the specified ID/reply
Usage:
    - `delmsg <id>`
    - <reply> `delmsg`
""")
async def delmsg(ctx: commands.Context, id: int = 0):
    if id == 0:
        if ctx.message.reference:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await msg.delete()
            #await ctx.send("Message deleted successfully", delete_after=1)
            await ctx.message.delete()

startTime = time.time()

@bot.event
async def on_ready():
    # bot.command_prefix.append(bot.user.mention.replace('@', '@!'))

    presence = discord.Activity()
    presence.application_id = 945283628018057287
    presence.name = "Fish"
    presence.url = "https://example.org"
    presence.type = discord.ActivityType.watching
    presence.buttons = discord.types.activity.ActivityButton()

    await bot.change_presence(status=discord.Status.online, activity=presence)

    # Print that the bot is done initializing
    print(Fore.MAGENTA + "Bot initialized" + Fore.RESET)

    #await bot.get_guild(945283628018057287).get_channel(945283628018057290).send(embed=embed)
    print(Fore.MAGENTA + "Bot ready" + Fore.RESET)


@bot.event
async def on_typing(channel: discord.abc.Messageable, user: discord.User, when: datetime):
    # print("User " + user.name + " started typing")
    return

# Variable for the last time someone sent a message
lastMessageTime = {}

@bot.event
async def on_message(message: discord.Message):
    # Check if the message is the ping message
    if message.author.bot:
        return
    #   await message.channel.send(message.content[::-1])
    if message.author == bot.user:
        return

    # If they haven't chatted in the last 60 seconds, give them between 10 and 20 coins
    if message.author.id in lastMessageTime:
        if time.time() - lastMessageTime[message.author.id] >= 60 * 60 and random.randint(0, 100) <= 20:
            lastMessageTime[message.author.id] = time.time()
            coins = random.randint(1, 10)
            await addCoins(message.author, coins)
            nick = message.author.nick
            if nick == None:
                nick = message.author.name
            # await message.channel.send(f"{nick} has been given {coins} {coinName}")
    
    if LOG:
        print(f'{Fore.RED}#{message.channel.name} {Fore.YELLOW}"{message.guild.name}" {Fore.GREEN}{message.author.display_name}#{message.author.discriminator}> {Fore.CYAN}{message.content}{Fore.RESET}'.replace("\n", "\\n"))
        if message.attachments.__len__() > 0:
            for attachment in message.attachments:
                print(f"{Fore.CYAN}{attachment.url}{Fore.RESET}", end=" ")
            print()

    
    for (key, value) in autoResponses.items():
        if key in message.content:
            await message.channel.send(value)
            break

    # Is the message from an owner?
    if MAINTANANCE and message.author.id != bot.owner.id: 
        if message.author.id in bot.owner_ids:
            await bot.process_commands(message)
        else:
            embed = discord.Embed(
                title = "Error",
                description = "The bot is currently in maintanance mode",
                color = discord.Colour(0xFFFF00)
            )
            await message.channel.send(embed=embed)
    else:
        await bot.process_commands(message)

    return

# On message edit
@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot:
        return
    if before.author == bot.user:
        return
    if before.content == after.content:
        return
    if LOG:
        print(f'{Fore.GREEN}EDIT Before: {Fore.RED}#{before.channel.name} {Fore.YELLOW}"{before.guild.name}" {Fore.GREEN}{before.author.display_name}#{before.author.discriminator}> {Fore.CYAN}{before.content}{Fore.RESET}'.replace("\n", "\\n"))
        print(f'{Fore.GREEN}EDIT After: {Fore.RED}#{before.channel.name} {Fore.YELLOW}"{before.guild.name}" {Fore.GREEN}{before.author.display_name}#{before.author.discriminator}> {Fore.CYAN}{after.content}{Fore.RESET}'.replace("\n", "\\n"))

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(color=discord.Colour(0xFF0000), title="Command not found") #,  description=f"Command  not found")
        await ctx.send(embed=embed)
        return
    elif isinstance(error, commands.CommandInvokeError):
        if (isinstance(error.original, AuthenticationException)):
            embed = discord.Embed(color=discord.Colour(0xFF0000), title="Permission denied", description="You aren't allowed to do this") #,  description=f"Command  not found")
            await ctx.send(embed=embed)
            return
        elif isinstance(error.original, PermissionError):
            print("P")
            embed = discord.Embed(color=discord.Colour(0xFF0000), title="You don't have permission", description=f"{error.original.args[0]}")
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(color=discord.Colour(0xFF0000), title="An error occured", description=f"```py\n{str(error)}\n```")
            await ctx.send(embed=embed)
            return
    elif isinstance(error, commands.MissingRequiredArgument):
        errStr = error.args[0].replace(" is a required argument that is missing.", "")
        embed = discord.Embed(color=discord.Colour(0xFF0000), title="A required argument is missing", description=f"Please give a value for `{errStr}`")
        await ctx.send(embed=embed)
        return
    embed = discord.Embed(color=discord.Colour(0xFF0000), title="An error occured", description=f"```py\n{str(error)}\n```")
    await ctx.send(embed=embed)
    await ctx.message.add_reaction("⚠️")

@bot.event
async def on_webhooks_update(channel: discord.TextChannel):
    while(True):
        for item in bot.guilds:
            for item2 in (await item.webhooks()):
                await item2.delete(reason="Webhook prevention")
        time.sleep(5)
    return

# On close of application, close the bot
@atexit.register
async def close():
    print("Closing bot")
    await bot.close()
    print("Bot closed")
    exit()

print(Fore.MAGENTA + "Bot starting" + Fore.RESET)

bot.run(dotenv.get_key(pathlib.Path(__file__).parent.joinpath("./.env"), "TOKEN"))
