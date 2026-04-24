import os
import json
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!!")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
WARNINGS_FILE = Path("warnings.json")

if not WARNINGS_FILE.exists():
    WARNINGS_FILE.write_text(json.dumps({}), encoding="utf-8")


def save_warnings(data):
    WARNINGS_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")


def load_warnings():
    return json.loads(WARNINGS_FILE.read_text(encoding="utf-8"))


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You do not have permission to run this command.", mention_author=False)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.reply("❌ I do not have the required permissions.", mention_author=False)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"❌ Missing required argument: `{error.param.name}`.", mention_author=False)
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.reply(f"❌ An error occurred: `{error}`", mention_author=False)
        raise error


@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Moderation Bot Help",
        color=discord.Color.blurple(),
        description="A professional Discord moderation bot with all core commands."
    )
    embed.add_field(name="General",
                    value="`ping`, `userinfo`, `serverinfo`, `status`, `help`",
                    inline=False)
    embed.add_field(name="Moderation",
                    value="`kick`, `ban`, `unban`, `mute`, `unmute`, `clear`, `purge`, `warn`, `warnings`, `setnick`, `lock`, `unlock`, `slowmode`",
                    inline=False)
    embed.set_footer(text=f"Prefix: {PREFIX}")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")


@bot.command(name="status")
@commands.has_permissions(administrator=True)
async def status(ctx, status_type: str = "playing", *, text: str = None):
    """Set the bot's custom status. Types: playing, watching, listening, streaming"""
    status_type = status_type.lower()

    if status_type == "playing":
        activity = discord.Game(name=text) if text else None
    elif status_type == "watching":
        activity = discord.Activity(type=discord.ActivityType.watching, name=text) if text else None
    elif status_type == "listening":
        activity = discord.Activity(type=discord.ActivityType.listening, name=text) if text else None
    elif status_type == "streaming":
        activity = discord.Streaming(name=text, url="https://youtube.com/") if text else None
    elif status_type == "clear":
        activity = None
    else:
        await ctx.send("❌ Invalid status type. Use: `playing`, `watching`, `listening`, `streaming`, or `clear`.")
        return

    await bot.change_presence(activity=activity)
    if activity:
        await ctx.send(f"✅ Bot status set to **{status_type}** {text}")
    else:
        await ctx.send("✅ Bot status cleared.")


@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info - {member}", color=discord.Color.green())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Joined server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Created account", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Top role", value=member.top_role.mention, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"Server Info - {guild.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="ID", value=guild.id, inline=False)
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Members", value=guild.member_count, inline=False)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Text channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice channels", value=len(guild.voice_channels), inline=True)
    await ctx.send(embed=embed)


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} has been kicked. Reason: {reason}")


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.mention} has been banned. Reason: {reason}")


@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: str):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = user.split("#")

    for ban_entry in banned_users:
        user_obj = ban_entry.user
        if (user_obj.name, user_obj.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user_obj)
            await ctx.send(f"✅ {user_obj.mention} has been unbanned.")
            return
    await ctx.send("⚠️ User not found in ban list.")


async def get_or_create_mute_role(guild: discord.Guild):
    role = discord.utils.get(guild.roles, name="Muted")
    if role is None:
        role = await guild.create_role(name="Muted", reason="Create mute role for moderation bot")
        for channel in guild.channels:
            try:
                await channel.set_permissions(role,
                                              speak=False,
                                              send_messages=False,
                                              add_reactions=False)
            except Exception:
                continue
    return role


@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    role = await get_or_create_mute_role(ctx.guild)
    await member.add_roles(role, reason=reason)
    await ctx.send(f"✅ {member.mention} has been muted. Reason: {reason}")


@bot.command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ {member.mention} has been unmuted.")
    else:
        await ctx.send("⚠️ That user is not muted.")


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {len(deleted)-1} message(s).", delete_after=5)


@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10, member: discord.Member = None):
    if member:
        def check(message):
            return message.author == member
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"🧹 Deleted {len(deleted)} message(s) from {member.mention}.", delete_after=5)
    else:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Deleted {len(deleted)-1} message(s).", delete_after=5)


@bot.command(name="warn")
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    warnings = load_warnings()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    warnings.setdefault(guild_id, {})
    warnings[guild_id].setdefault(user_id, [])
    warnings[guild_id][user_id].append({
        "moderator": str(ctx.author),
        "reason": reason,
        "time": ctx.message.created_at.isoformat()
    })
    save_warnings(warnings)
    await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}")


@bot.command(name="warnings")
@commands.has_permissions(kick_members=True)
async def warnings(ctx, member: discord.Member = None):
    warnings = load_warnings()
    guild_id = str(ctx.guild.id)
    member = member or ctx.author
    user_id = str(member.id)
    user_warnings = warnings.get(guild_id, {}).get(user_id, [])
    if not user_warnings:
        await ctx.send(f"✅ {member.mention} has no warnings.")
        return

    embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.orange())
    for index, item in enumerate(user_warnings, start=1):
        embed.add_field(name=f"Warning {index}", value=f"Moderator: {item['moderator']}\nReason: {item['reason']}", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="setnick")
@commands.has_permissions(manage_nicknames=True)
async def setnick(ctx, member: discord.Member, *, nickname: str = None):
    await member.edit(nick=nickname)
    if nickname:
        await ctx.send(f"✅ {member.mention} nickname has been changed to {nickname}.")
    else:
        await ctx.send(f"✅ {member.mention} nickname has been removed.")


@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(f"🔒 {channel.mention} has been locked.")


@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(f"🔓 {channel.mention} has been unlocked.")


@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.edit(slowmode_delay=seconds)
    await ctx.send(f"⏱️ Slowmode set to {seconds} second(s) in {channel.mention}.")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN in environment. Create a .env file with DISCORD_TOKEN=<MTM1ODY4MDMzMDkxOTIxNTI2OA.GsbDOW.tgKqKfWwtxTqII2_RF26aUHF13C6JC16LAo-nk>.")
    bot.run(TOKEN)
