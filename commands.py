import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ROLE_ID, PROTECTED_CHANNEL_IDS

def setup_commands(bot, load_database, save_database, generate_new_key, transfer_key_to_user, pick_random_member):
    
    # Admin check
    def is_admin(interaction: discord.Interaction) -> bool:
        return interaction.guild and any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)
    
    # Show the current key
    @bot.tree.command(name="showkey", description="Show the current key (Admin only)")
    async def show_key(interaction: discord.Interaction):
        if not is_admin(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        db = load_database()
        if db["key"]:
            embed = discord.Embed(
                title="🔑 Current Key",
                description=f"The current key is: ||{db['key']}||",
                color=0x00ff00
            )
            
            if db["current_key_holder"]:
                embed.add_field(name="Current Holder", value=f"<@{db['current_key_holder']}>", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("No key has been generated yet.", ephemeral=True)

    # Generate a new key and assign it to a random member
    @bot.tree.command(name="newkey", description="Generate a new key and assign it to a random member (Admin only)")
    async def new_key(interaction: discord.Interaction):
        if not is_admin(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        guild = interaction.guild
        db = load_database()
        
        # Generate new key
        db["key"] = generate_new_key()
        save_database(db)
        
        # Choose random member and assign key
        user_id = await pick_random_member(guild)
        if user_id:
            await interaction.response.send_message("Generating new key and assigning to a random member...", ephemeral=True)
            await transfer_key_to_user(user_id, guild, reason="Admin Generated New Key")
        else:
            await interaction.response.send_message("Failed to find a valid member to assign the key.", ephemeral=True)

    # Manually transfer the key to a specific member
    @bot.tree.command(name="transferkey", description="Transfer the key to a specific member (Admin only)")
    @app_commands.describe(member="The member to transfer the key to")
    async def transfer_key(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        if member.bot:
            await interaction.response.send_message("Cannot transfer key to a bot.", ephemeral=True)
            return
            
        guild = interaction.guild
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        
        if admin_role in member.roles:
            await interaction.response.send_message("Cannot transfer key to an admin.", ephemeral=True)
            return
            
        await interaction.response.send_message(f"Transferring key to {member.mention}...", ephemeral=True)
        await transfer_key_to_user(member.id, guild, reason=f"Manual Transfer by {interaction.user.name}")

    # Force a random key transfer now
    @bot.tree.command(name="forcetransfer", description="Force a random key transfer now (Admin only)")
    async def force_transfer(interaction: discord.Interaction):
        if not is_admin(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        guild = interaction.guild
        user_id = await pick_random_member(guild)
        if user_id:
            await interaction.response.send_message("Forcefully transferring key to a random member...", ephemeral=True)
            await transfer_key_to_user(user_id, guild, reason=f"Forced Transfer by {interaction.user.name}")
        else:
            await interaction.response.send_message("Failed to find a valid member to transfer the key to.", ephemeral=True)

    # View transfer history
    @bot.tree.command(name="history", description="View key transfer history (Admin only)")
    @app_commands.describe(limit="Number of transfer entries to view (default: 10)")
    async def view_history(interaction: discord.Interaction, limit: int = 10):
        if not is_admin(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        db = load_database()
        history = db.get("transfer_history", [])
        
        if not history:
            await interaction.response.send_message("No transfer history available.", ephemeral=True)
            return
            
        # Limit the number of entries to display
        history = history[-limit:] if len(history) > limit else history
        
        embed = discord.Embed(
            title="🔑 Key Transfer History",
            color=0x00ff00,
            description=f"Showing last {len(history)} transfers"
        )
        
        for i, entry in enumerate(reversed(history), 1):
            timestamp = entry.get("timestamp", "Unknown time")
            new_holder = entry.get("new_holder", "Unknown")
            reason = entry.get("reason", "Unknown reason")
            
            embed.add_field(
                name=f"{i}. {timestamp}",
                value=f"Transferred to: <@{new_holder}>\nReason: {reason}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Let anyone check if they are the key holder
    @bot.tree.command(name="amikeyowner", description="Check if you are the current key holder")
    async def am_i_key_owner(interaction: discord.Interaction):
        db = load_database()
        if str(interaction.user.id) == str(db.get("current_key_holder")):
            await interaction.response.send_message(f"Yes, {interaction.user.mention}, you are the current key holder! 🔑", ephemeral=True)
        else:
            await interaction.response.send_message(f"No, {interaction.user.mention}, you are not the current key holder.", ephemeral=True)

    # A command for the key holder to verify their key
    @bot.tree.command(name="verifykey", description="Verify your key if you are the key holder")
    @app_commands.describe(key="Your key to verify")
    async def verify_key(interaction: discord.Interaction, key: str):
        db = load_database()
        if str(interaction.user.id) == str(db.get("current_key_holder")) and key == db.get("key"):
            await interaction.response.send_message("Key verified! You are indeed the rightful key holder. 🔑", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid key or you are not the key holder.", ephemeral=True)

    # Error handler for app commands
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, app_commands.errors.MissingRequiredArgument):
            await interaction.response.send_message(f"Missing required argument.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)
