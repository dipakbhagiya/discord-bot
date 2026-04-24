# Discord Moderation Bot

A professional Discord moderation bot built with `discord.py`.

## Features
- Kick, ban, unban
- Mute, unmute
- Clear messages
- Purge messages (with user filtering)
- Warn users and list warnings
- Set nicknames
- Lock / unlock channels
- Slowmode control
- Custom status setting
- User info and server info
- Custom help command

## Setup
1. Install Python 3.11+.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your bot token.
5. Run the bot:
   ```powershell
   python bot.py
   ```

## Permissions
The bot needs the following permissions in your server:
- Manage Roles
- Kick Members
- Ban Members
- Manage Messages
- Manage Channels
- Send Messages
- Read Message History

## Example commands
- `!help`
- `!ping`
- `!status playing Moderating servers`
- `!status watching over the server`
- `!status clear`
- `!kick @user reason`
- `!ban @user reason`
- `!unban username#1234`
- `!mute @user reason`
- `!unmute @user`
- `!clear 15`
- `!purge 15`
- `!purge 15 @user`
- `!warn @user reason`
- `!warnings @user`
- `!setnick @user NewName`
- `!lock`
- `!unlock`
- `!slowmode 10`
