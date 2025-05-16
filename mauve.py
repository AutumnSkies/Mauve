import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import logging
import os
import re
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = '''You probably shouldn't use this if you don't know what it does.
En masse role replacer made by stylisticallycatgirl (Sadie). Special thanks to Amby and the Rain Discord!'''

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

        # Hardcoded legacy role priority (top = highest priority)
        legacy_role_priority = [
            ".Ask",
            ".Name is pronoun",
            ".Any Pronouns",
            ".It/It/Its",
            ".Fae/Faer/Faers",
            ".Ae/Aer",
            ".They/Them/Theirs",
            ".He/Him/His",
            ".She/Her/Hers",
            ".Not She/Her/Hers",
            ".Not He/Him/His",
        ]

        for member in guild.members:
            # Find legacy roles the member currently has
            member_legacy_roles = [r for r in member.roles if r.name in role_mappings]
            if not member_legacy_roles:
                continue

            # Map role name to role object for easy lookup
            legacy_roles_by_name = {r.name: r for r in member_legacy_roles}

            # Find the highest-priority legacy role from our hardcoded list
            top_legacy_name = None
            for name in legacy_role_priority:
                if name in legacy_roles_by_name:
                    top_legacy_name = name
                    break

            if not top_legacy_name:
                continue  # Something went wrong, skip this member

            removed_roles = member_legacy_roles.copy()
            added_pronouns = []

            # Always add pronoun roles mapped from all legacy roles
            for legacy_role in member_legacy_roles:
                pronoun_name, _ = role_mappings[legacy_role.name]
                pronoun_role = discord.utils.get(guild.roles, name=pronoun_name)
                if pronoun_role and pronoun_role not in member.roles:
                    added_pronouns.append(pronoun_role)

            # Add color role from top-priority legacy role
            _, top_color_name = role_mappings[top_legacy_name]
            added_color = discord.utils.get(guild.roles, name=top_color_name)
            roles_to_add = added_pronouns.copy()
            if added_color and added_color not in member.roles:
                roles_to_add.append(added_color)

            log_msg = f"{member.id} remove {[r.name for r in removed_roles]} add {[r.name for r in roles_to_add]}"
            update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} {log_msg}")
            all_updates.append(log_msg)
            print(f"[✓] {log_msg}")

            if not is_dry_run:
                await member.remove_roles(*removed_roles)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)

        # Send results in batches
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
        await ctx.send("  Done!")

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
    missing_messages = []

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
            embed.set_footer(text="Mapping: Legacy → Pronoun, Color")
            embed.add_field(name="Legacy Role", value=legacy, inline=True)
            embed.add_field(name="Pronoun Role", value=pronoun, inline=True)
            embed.add_field(name="Color Role", value=color, inline=True)
            missing_messages.append(embed)

    if found_all:
        await ctx.send("All expected roles are present!")
    else:
        for embed in missing_messages:
            await ctx.send(embed=embed)

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

@bot.command()
@commands.has_role("MauvePermissions")
async def assign_legacy_roles(ctx, mode: str = None):
    is_dry_run = mode == "dry"
    guild = ctx.guild
    all_members = [m for m in guild.members if not m.bot]
    legacy_role_names = list(role_mappings.keys())

    if len(all_members) < 50:
        await ctx.send("❌ Not enough members to assign roles to 50 users.")
        return

    selected_members = random.sample(all_members, 50)
    assigned_log = []

    update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} [LEGACY_ASSIGN] started by {ctx.author} in guild '{guild.name}'")

    for member in selected_members:
        role_count = random.randint(1, 5)
        chosen_role_names = random.sample(legacy_role_names, role_count)

        roles_to_add = []
        added_names = []

        for role_name in chosen_role_names:
            role = discord.utils.get(guild.roles, name=role_name)
            if role and role not in member.roles:
                roles_to_add.append(role)
                added_names.append(role.name)

        if roles_to_add:
            log_entry = f"{member.id} remove [] add {added_names}"
            update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} {log_entry}")
            assigned_log.append(f"{member.name} <- {added_names}")

            if not is_dry_run:
                try:
                    await member.add_roles(*roles_to_add)
                except discord.Forbidden:
                    assigned_log[-1] += " ❌ Permission error"
                except Exception as e:
                    assigned_log[-1] += f" ⚠️ Error: {e}"

    if not assigned_log:
        await ctx.send("No roles were assigned.")
        return

    embed = discord.Embed(
        title="🧾 Legacy Role Assignment (Dry Run)" if is_dry_run else "✅ Legacy Roles Assigned",
        description="\n".join(assigned_log[:10]) + ("\n... (truncated)" if len(assigned_log) > 10 else ""),
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

    try:
        with open(update_log_path, 'rb') as f:
            await ctx.send("📄 Here's the full update log:", file=discord.File(f, filename='role_updates.log'))
    except Exception as e:
        await ctx.send(f"⚠️ Could not upload the log: {e}")


# Run the bot
bot.run(TOKEN, log_handler=handler)
