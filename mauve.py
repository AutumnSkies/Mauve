import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import logging
import os
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = '''You probably shouldn't use this if you don't know what it does.
En masse role replacer made by stylisticallycatgirl (Sadie). Special thanks to Pea, Diane and all the rest on the rain discord for help!
If you're having issues with permissions did you create and assign the "MauvePermissions" role?'''

bot = commands.Bot(command_prefix='m;', description=description, intents=intents)

# Set presence and ensure permissions role exists
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="Lavender is such a pretty color"))

    role_name = "MauvePermissions"
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try:
                await guild.create_role(name=role_name, reason="Role needed for specific permissions")
                print(f"Created role `{role_name}` in `{guild.name}`")
            except discord.Forbidden:
                print(f"Missing permissions to create role in `{guild.name}`")

# Handle missing permissions
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You lack the `MauvePermissions` role to use this command.")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Mauve')
handler = logging.FileHandler(filename='Mauve.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Role update log
update_log_path = 'role_updates.log'
update_logger = logging.getLogger('RoleUpdates')
update_logger.setLevel(logging.INFO)
update_handler = logging.FileHandler(filename=update_log_path, encoding='utf-8', mode='a')
update_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
update_logger.addHandler(update_handler)

# Role mapping (legacy -> (new_pronoun, new_color))
role_mappings = {
    ".Ask": ("Ask", "Slate"),
    ".Name is pronoun": ("Name is pronoun", "Teal"),
    ".Any Pronouns": ("Any Pronouns", "Peach"),
    ".It/It/Its": ("It/Its/Its", "Slate"),
    ".Fae/Faer/Faers": ("Fae/Faer/Faers", "Helio"),
    ".Ae/Aer": ("Ae/Aer", "Raspberry"),
    ".Vi/Ver/Vers": ("Vi/Ver/Vers", "Black"),
    ".They/Them/Theirs": ("They/Them/Theirs", "Electric Purple"),
    ".He/Him/His": ("He/Him/His", "Sapphire"),
    ".She/Her/Hers": ("She/Her/Hers", "Bubblegum"),
    ".Not She/Her/Hers": ("Not She/Her/Hers", "Peach"),
    ".Not He/Him/His": ("Not He/Him/His", "Orange"),
}

@bot.command()
@commands.has_role("MauvePermissions")
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command()
@commands.has_role("MauvePermissions")
async def update_roles(ctx, mode: str = None):
    is_dry_run = mode == "dry"
    confirmation_message = await ctx.send(
        f"{'Dry run' if is_dry_run else 'Real update'} requested. React with ✅ to confirm or ❌ to cancel."
    )
    await confirmation_message.add_reaction("✅")
    await confirmation_message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        if str(reaction.emoji) != "✅":
            await ctx.send("❌ Canceled.")
            return

        await ctx.send("Confirmed. Processing...")

        guild = ctx.guild
        all_updates = []
        update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} started by {ctx.author} in guild '{guild.name}'")

        for member in guild.members:
            legacy_roles = [r for r in member.roles if r.name in role_mappings]
            if not legacy_roles:
                continue

            legacy_roles.sort(key=lambda r: r.position, reverse=True)
            added_pronouns = []
            added_color = None
            removed_roles = []

            top_color_set = False
            for legacy_role in legacy_roles:
                pronoun, color = role_mappings[legacy_role.name]
                pronoun_role = discord.utils.get(guild.roles, name=pronoun)
                color_role = discord.utils.get(guild.roles, name=color)

                removed_roles.append(legacy_role)
                if pronoun_role and pronoun_role not in member.roles:
                    added_pronouns.append(pronoun_role)
                if not top_color_set and color_role and color_role not in member.roles:
                    added_color = color_role
                    top_color_set = True

            roles_to_add = added_pronouns.copy()
            if added_color:
                roles_to_add.append(added_color)

            log_msg = f"{member.id} remove {[r.name for r in removed_roles]} add {[r.name for r in roles_to_add]}"
            update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} {log_msg}")
            all_updates.append(log_msg)
            print(f"[✓] {log_msg}")

            if not is_dry_run:
                await member.remove_roles(*removed_roles)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)

        chunk_size = 10
        for i in range(0, len(all_updates), chunk_size):
            chunk = all_updates[i:i + chunk_size]
            embed = discord.Embed(
                title="Dry Run Preview" if is_dry_run else "Updated Members",
                description="\n".join(chunk),
                color=discord.Color.purple()
            )
            await ctx.send(embed=embed)

        update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} completed. {len(all_updates)} members processed.")
        await ctx.send("✅ Done!")

        try:
            with open(update_log_path, 'rb') as f:
                await ctx.send("📄 Here's the full update log:", file=discord.File(f, filename='role_updates.log'))
        except Exception as e:
            await ctx.send(f"⚠️ Could not upload the log: {e}")

    except asyncio.TimeoutError:
        await ctx.send("⌛ Timeout.")

@bot.command()
@commands.has_role("MauvePermissions")
async def rollback(ctx, mode: str = None):
    is_dry_run = mode == "dry"
    if not os.path.exists(update_log_path):
        await ctx.send("❌ No log file found for rollback.")
        return

    await ctx.send("Rollback initiated. This may take a moment...")

    rollback_count = 0
    with open(update_log_path, 'r', encoding='utf-8') as log_file:
        for line in log_file:
            if "[UPDATE]" not in line or "remove" not in line:
                continue
            try:
                member_id = int(re.search(r"(\d+)\sremove", line).group(1))
                remove_roles = re.search(r"remove \[(.*?)\]", line).group(1).replace("'", "").split(", ")
                add_roles = re.search(r"add \[(.*?)\]", line).group(1).replace("'", "").split(", ")
            except Exception:
                continue

            member = ctx.guild.get_member(member_id)
            if not member:
                continue

            roles_to_add = [discord.utils.get(ctx.guild.roles, name=r) for r in remove_roles if discord.utils.get(ctx.guild.roles, name=r)]
            roles_to_remove = [discord.utils.get(ctx.guild.roles, name=r) for r in add_roles if discord.utils.get(ctx.guild.roles, name=r)]

            log_msg = f"Rollback for {member.name}: add {[r.name for r in roles_to_add]}, remove {[r.name for r in roles_to_remove]}"
            update_logger.info(f"{'[DRY ROLLBACK]' if is_dry_run else '[ROLLBACK]'} {log_msg}")
            print(f"[↩] {log_msg}")
            rollback_count += 1

            if not is_dry_run:
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)

    # Handle created role deletions
    role_creation_path = 'created_roles.log'
    created_roles = []
    if os.path.exists(role_creation_path):
        with open(role_creation_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(r".*\[CREATED_ROLE\] (\d+):(.+)", line)
                if match and match.group(1) == str(ctx.guild.id):
                    created_roles.append(match.group(2))

    deleted_roles = []
    for role_name in created_roles:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            try:
                if not is_dry_run:
                    await role.delete(reason="Rollback of created role")
                deleted_roles.append(role_name)
            except Exception as e:
                await ctx.send(f"⚠️ Could not delete role `{role_name}`: {e}")

    await ctx.send(f"✅ Rollback {'dry run' if is_dry_run else 'complete'} — {rollback_count} member entries processed.")
    if deleted_roles:
        await ctx.send(f"🗑️ Deleted roles: {', '.join(deleted_roles)}")

    try:
        with open(update_log_path, 'rb') as f:
            await ctx.send("📄 Here's the updated log file:", file=discord.File(f, filename='role_updates.log'))
    except Exception as e:
        await ctx.send(f"⚠️ Could not upload the log: {e}")

@bot.command()
async def list(ctx):
    if ctx.author.id != 1191948659160518656:
        await ctx.send("❌ You are not authorized to use this command.")
        return

    server_list = "\n".join([f"{guild.name} (ID: {guild.id})" for guild in bot.guilds])
    await ctx.send(f"📋 The bot is in the following servers:\n```{server_list}```")

@bot.command()
@commands.has_role("MauvePermissions")
async def check(ctx):
    guild = ctx.guild
    found_all = True

    for legacy, (pronoun, color) in role_mappings.items():
        missing = []
        for role_name in [legacy, pronoun, color]:
            if not discord.utils.get(guild.roles, name=role_name):
                missing.append(role_name)

        if missing:
            found_all = False
            embed = discord.Embed(
                title="⚠️ Missing Roles",
                description="\n".join(f"❌ {r}" for r in missing),
                color=discord.Color.purple()
            )
        else:
            embed = discord.Embed(
                title="✅ All Present",
                description=f"All roles found:\n• {legacy}\n• {pronoun}\n• {color}",
                color=discord.Color.purple()
            )
        
        embed.set_footer(text="Mapping: Legacy → Pronoun, Color")
        embed.add_field(name="Legacy Role", value=legacy, inline=True)
        embed.add_field(name="Pronoun Role", value=pronoun, inline=True)
        embed.add_field(name="Color Role", value=color, inline=True)

        await ctx.send(embed=embed)

    if found_all:
        await ctx.send("All expected roles are present!")

@bot.command()
@commands.has_role("MauvePermissions")
async def create_missing_roles(ctx):
    guild = ctx.guild
    created_roles = []

    # Setup logger for created roles
    role_logger = logging.getLogger('RoleCreations')
    role_logger.setLevel(logging.INFO)
    role_creation_path = 'created_roles.log'
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(role_creation_path) for h in role_logger.handlers):
        role_creation_handler = logging.FileHandler(filename=role_creation_path, encoding='utf-8', mode='a')
        role_creation_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        role_logger.addHandler(role_creation_handler)

    for legacy, (pronoun, color) in role_mappings.items():
        for role_name in [legacy, pronoun, color]:
            if not discord.utils.get(guild.roles, name=role_name):
                try:
                    await guild.create_role(name=role_name, reason="Auto-created from Mauve role mapping")
                    created_roles.append(role_name)
                    role_logger.info(f"[CREATED_ROLE] {guild.id}:{role_name}")
                except discord.Forbidden:
                    await ctx.send(f"❌ Missing permissions to create role `{role_name}`")
                except Exception as e:
                    await ctx.send(f"⚠️ Error creating role `{role_name}`: {e}")

    if created_roles:
        embed = discord.Embed(
            title="🆕 Created Missing Roles",
            description="\n".join(created_roles),
            color=discord.Color.purple()
        )
    else:
        embed = discord.Embed(
            title="✅ All Roles Present",
            description="No missing roles found in this server.",
            color=discord.Color.purple()
        )

    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN, log_handler=handler)
