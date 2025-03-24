import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import datetime
import random
import os
import asyncio
from commands import setup_commands
from config import (
    TOKEN, TRANSFER_INTERVAL_HOURS, PROTECTED_CHANNEL_IDS, 
    ADMIN_ROLE_ID, KEY_HOLDER_ROLE_ID, BOT_LOG_CHANNEL_ID
)

# Set up intents for the bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Initialize bot with intents
bot = commands.Bot(command_prefix="/", intents=intents)

# Database operations
def load_database():
    if os.path.exists('database.json'):
        with open('database.json', 'r') as f:
            return json.load(f)
    else:
        return {
            "current_key_holder": None,
            "key": None,
            "transfer_history": [],
            "last_transfer": None
        }

def save_database(data):
    with open('database.json', 'w') as f:
        json.dump(data, f, indent=4)

# Generate a new random key
def generate_new_key():
    key_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    key = ''.join(random.choice(key_chars) for _ in range(16))
    return key

# Key transfer logic
async def transfer_key_to_user(user_id, guild, reason="Scheduled Transfer"):
    db = load_database()
    old_holder_id = db["current_key_holder"]
    
    # Generate a new key if there isn't one
    if not db["key"]:
        db["key"] = generate_new_key()
    
    # Update database with new holder
    db["current_key_holder"] = user_id
    db["last_transfer"] = datetime.datetime.now().isoformat()
    db["transfer_history"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "new_holder": user_id,
        "previous_holder": old_holder_id,
        "reason": reason
    })
    save_database(db)
    
    # Update roles
    key_holder_role = guild.get_role(KEY_HOLDER_ROLE_ID)
    
    # Remove role from previous holder if they exist
    if old_holder_id:
        try:
            old_holder = await guild.fetch_member(int(old_holder_id))
            if old_holder and key_holder_role in old_holder.roles:
                await old_holder.remove_roles(key_holder_role)
        except discord.errors.NotFound:
            pass  # Previous holder may have left the server
    
    # Add role to new holder
    new_holder = await guild.fetch_member(int(user_id))
    await new_holder.add_roles(key_holder_role)
    
    # Send notification to log channel
    log_channel = guild.get_channel(BOT_LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="🔑 Key Transfer",
            description=f"The key has been transferred to <@{user_id}>",
            color=0x00ff00,
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Key", value=f"||{db['key']}||", inline=False)
        await log_channel.send(embed=embed)
    
    # DM the new key holder
    try:
        embed = discord.Embed(
            title="🎉 You've received the key!",
            description="You are now the holder of the server key!",
            color=0x00ff00
        )
        embed.add_field(name="Your Key", value=f"||{db['key']}||", inline=False)
        embed.add_field(name="Information", value="This key grants you special access to certain channels in the server. Keep it safe! The key will be automatically transferred to someone else later.", inline=False)
        await new_holder.send(embed=embed)
    except discord.errors.Forbidden:
        # User might have DMs disabled
        pass
    
    # Announce in server
    for channel_id in PROTECTED_CHANNEL_IDS:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(f"🔑 <@{user_id}> is now the key holder and has access to this channel!")

# Pick a random member (excluding bots and members with admin role)
async def pick_random_member(guild):
    valid_members = []
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    
    for member in guild.members:
        # Skip bots and members with admin role
        if not member.bot and admin_role not in member.roles:
            valid_members.append(member)
    
    if valid_members:
        return random.choice(valid_members).id
    return None

@tasks.loop(hours=TRANSFER_INTERVAL_HOURS)
async def scheduled_key_transfer():
    for guild in bot.guilds:
        user_id = await pick_random_member(guild)
        if user_id:
            await transfer_key_to_user(user_id, guild)

@scheduled_key_transfer.before_loop
async def before_key_transfer():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'Bot is logged in as {bot.user}')
    
    # Sync commands with Discord
    print("Syncing commands with Discord...")
    await bot.tree.sync()
    print("Commands synced!")
    
    # Set up the key transfer loop
    scheduled_key_transfer.start()
    
    # If the bot just started, transfer the key to a new random user
    for guild in bot.guilds:
        db = load_database()
        user_id = await pick_random_member(guild)
        if user_id:
            await transfer_key_to_user(user_id, guild, reason="Bot Restart")

# Setup commands from commands.py
setup_commands(bot, load_database, save_database, generate_new_key, transfer_key_to_user, pick_random_member)

# Run the bot
bot.run(TOKEN)
