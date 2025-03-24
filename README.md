# Discord Key Rotation Bot

A unique Discord bot that implements a key rotation system where a single key is automatically transferred to random members, granting them special access to protected channels.

## Features

- **Single Key System**: Only one key exists in the entire server at any time
- **Automatic Key Rotation**: Key transfers to a random server member every 24 hours
- **Admin Control**: Administrators can manage keys and trigger transfers
- **Role Management**: Automatic role updates when keys are transferred
- **Transfer Logging**: Complete history of key transfers
- **Restart Protection**: Key is reassigned on bot restart

## Setup

### Requirements
- Python 3.8+
- discord.py library

### Installation

1. Clone this repository or download the files
2. Install required packages:
   ```
   pip install discord.py
   ```
3. Configure the bot in `config.py`:
   - Add your Discord bot token
   - Configure the key transfer interval
   - Add your server's role IDs for admin and key holder roles
   - Add the channel IDs for protected channels and the bot log channel

4. Run the bot:
   ```
   python bot.py
   ```

## Configuration

Edit the `config.py` file to customize the bot:

```python
# Bot Token
TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

# Key Transfer Settings (in hours)
TRANSFER_INTERVAL_HOURS = 24  # Default: 24 hours

# Role IDs (replace with your server's role IDs)
ADMIN_ROLE_ID = 0  # Admin role that can manage keys
KEY_HOLDER_ROLE_ID = 0  # Role assigned to key holders

# Channel IDs (replace with your server's channel IDs)
BOT_LOG_CHANNEL_ID = 0  # Channel for bot logs
PROTECTED_CHANNEL_IDS = [0, 0, 0]  # Channels that require key access
```

## Server Setup

1. Create two roles in your Discord server:
   - Admin role (for those who can manage the key)
   - Key Holder role (automatically assigned to members who receive the key)

2. Set up channel permissions:
   - For protected channels, deny view/read permissions to @everyone
   - Grant view/read permissions to the Key Holder role and Admin role
   - This ensures only the key holder and admins can access these channels

## Slash Commands

### Admin Commands

- `/showkey` - Shows the current key and who holds it
- `/newkey` - Generates a new key and assigns it to a random member
- `/transferkey @user` - Transfers the key to a specific member
- `/forcetransfer` - Forces an immediate random key transfer
- `/history [limit]` - Shows key transfer history (default: last 10 transfers)

### User Commands

- `/amikeyowner` - Checks if you are the current key holder
- `/verifykey [key]` - Verifies if your key is correct

## How It Works

1. The bot automatically transfers the key to a random member every 24 hours (configurable)
2. When a member receives the key, they're:
   - Assigned the Key Holder role
   - Notified via DM with their key
   - Announced in the protected channels
3. The key automatically grants access to protected channels through Discord's role permissions
4. Admins can generate new keys or force transfers at any time
5. When the bot restarts, it transfers the key to a new random member

## Troubleshooting

- **Bot not responding**: Ensure the token in `config.py` is correct
- **Permission issues**: Make sure the bot has the necessary permissions (Manage Roles, Send Messages)
- **Commands not appearing**: Make sure to wait a few minutes after adding the bot for slash commands to register
- **Role not being assigned**: Ensure the bot's role is higher in the hierarchy than the Key Holder role

## Important Bot Permissions

The bot requires these permissions:
- Manage Roles
- View Channels
- Send Messages
- Embed Links
- Use Slash Commands
- Read Message History

## License
