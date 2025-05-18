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
I do a lot of things, but I was made by Sadie (StylisticallyCatgirl)'''

bot = commands.Bot(command_prefix='m;', description=description, intents=intents)

# Mappings for roles

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
# Priorities for color roles - I'm aware this shouldn't be hardcoded but I can't get it to work properly without it
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

# For assinging random roles for the test commands
legacy_roles = [
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

# Logging setup

# Basic Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Mauve')
handler = logging.FileHandler(filename='Mauve.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Rollback update logging
update_log_path = 'role_updates.log'
update_logger = logging.getLogger('RoleUpdates')
update_logger.setLevel(logging.INFO)
update_handler = logging.FileHandler(filename=update_log_path, encoding='utf-8', mode='a')
update_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
update_logger.addHandler(update_handler)

# Logging for created roles
role_logger = logging.getLogger('RoleCreations')
role_logger.setLevel(logging.INFO)
role_creation_path = 'created_roles.log'
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(role_creation_path) for h in role_logger.handlers):
    role_creation_handler = logging.FileHandler(filename=role_creation_path, encoding='utf-8', mode='a')
    role_creation_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    role_logger.addHandler(role_creation_handler)

backup_dir = "backups"
os.makedirs(backup_dir, exist_ok=True)


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
                await guild.create_role(name=role_name, reason="Required to operate Mauve")
                print(f"Created role `{role_name}` in `{guild.name}`")
            except discord.Forbidden:
                print(f"Missing permissions to create role in `{guild.name}`")

# Handle missing permissions

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You lack the `MauvePermissions` role, which is necessary for all functions of Mauve.")

# Beacuse sometimes you just wanna play a game of ping pong

@bot.command()
@commands.has_role("MauvePermissions")
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# The command that actually does what the bot is for

@bot.command(name="update_roles")
@commands.has_role("MauvePermissions")
async def update_roles(ctx, mode: str = None):
    """Updates legacy roles to pronoun and color roles. Requires --dry-run or --execute."""
    guild = ctx.guild
    channel = ctx.channel

    if mode not in ["--dry-run", "--execute"]:
        await channel.send("❌ Please specify a mode: `--dry-run` to simulate or `--execute` to apply changes.\nExample: `m;update_roles --dry-run`")
        return

    dry_run = mode == "--dry-run"
    await channel.send(f"{'Dry-running' if dry_run else 'Executing'} role update for guild: {guild.name}...")

    # Validate mappings and existing roles
    missing_roles = set()
    for legacy_role, (pronoun_role, color_role) in role_mappings.items():
        if discord.utils.get(guild.roles, name=legacy_role) is None:
            missing_roles.add(legacy_role)
        if discord.utils.get(guild.roles, name=pronoun_role) is None:
            missing_roles.add(pronoun_role)
        if discord.utils.get(guild.roles, name=color_role) is None:
            missing_roles.add(color_role)

    if missing_roles:
        await channel.send(f"Missing roles: {', '.join(missing_roles)}. Use `m;create_missing_roles` to create them.")
        return

    legacy_roles_set = set(role_mappings.keys())

    for member in guild.members:
        if member.bot:
            continue

        legacy_roles = [role for role in member.roles if role.name in legacy_roles_set]
        if not legacy_roles:
            continue

        legacy_roles_sorted = sorted(legacy_roles, key=lambda r: legacy_role_priority.index(r.name))
        top_legacy = legacy_roles_sorted[0].name

        pronoun_roles_to_add = []
        color_role_to_add = None

        for legacy_role in legacy_roles:
            pronoun, _ = role_mappings[legacy_role.name]
            pronoun_role_obj = discord.utils.get(guild.roles, name=pronoun)
            if pronoun_role_obj:
                pronoun_roles_to_add.append(pronoun_role_obj)

        _, color_role = role_mappings[top_legacy]
        color_role_obj = discord.utils.get(guild.roles, name=color_role)

        roles_to_remove = legacy_roles
        roles_to_add = pronoun_roles_to_add
        if color_role_obj:
            roles_to_add.append(color_role_obj)

        if dry_run:
            status = f"[Dry run] Would update {member.mention}: remove {[r.name for r in roles_to_remove]}, add {[r.name for r in roles_to_add]}"
        else:
            try:
                await member.remove_roles(*roles_to_remove, reason="Mauve pronoun migration")
                await member.add_roles(*roles_to_add, reason="Mauve pronoun migration")
                status = f"Updated {member.mention}: removed {[r.name for r in roles_to_remove]}, added {[r.name for r in roles_to_add]}"
            except Exception as e:
                status = f"❌ Error updating {member.mention}: {str(e)}"

        await channel.send(status)
        await asyncio.sleep(0.5)  # optional delay to avoid hitting rate limits

    await channel.send("Role update completed.")



# Probably best practice to have this here

@bot.command()
@commands.has_role("MauvePermissions")
async def backup_roles(ctx):
    guild = ctx.guild
    relevant_roles = set(role_mappings.keys()) | {
        pronoun for pronoun, _ in role_mappings.values()
    } | {
        color for _, color in role_mappings.values()
    }

    backup_path = os.path.join(backup_dir, f"{guild.id}.log")

    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            for member in guild.members:
                member_roles = [r.name for r in member.roles if r.name in relevant_roles]
                if member_roles:
                    f.write(f"{member.id}:{','.join(member_roles)}\n")
        await ctx.send(f"Backup complete. Saved relevant role data for `{guild.name}`.")
    except Exception as e:
        await ctx.send(f"Could not create backup: {e}")


# In theory this should save all our collective asses if I mess up

@bot.command()
@commands.has_role("MauvePermissions")
async def rollback(ctx, mode: str = None):
    is_dry_run = mode == "dry"
    is_restore = mode == "restore"
    guild = ctx.guild

    if is_restore:
        backup_path = os.path.join(backup_dir, f"{guild.id}.log")

        if not os.path.exists(backup_path):
            await ctx.send(f"No backup found for `{guild.name}`.")
            return

        await ctx.send("Restoring from backup. This may take a bit...")

        relevant_roles = set(role_mappings.keys()) | {
            pronoun for pronoun, _ in role_mappings.values()
        } | {
            color for _, color in role_mappings.values()
        }

        restored = 0
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' not in line:
                        continue
                    member_id_str, roles_csv = line.strip().split(":", 1)
                    role_names = roles_csv.split(",")
                    member = guild.get_member(int(member_id_str))
                    if not member:
                        continue

                    current_affectable_roles = [r for r in member.roles if r.name in relevant_roles]
                    desired_roles = [discord.utils.get(guild.roles, name=name) for name in role_names]
                    desired_roles = [r for r in desired_roles if r is not None]

                    try:
                        if current_affectable_roles:
                            await member.remove_roles(*current_affectable_roles, reason="Restoring backup roles")
                        if desired_roles:
                            await member.add_roles(*desired_roles, reason="Restoring backup roles")
                        restored += 1
                    except Exception as e:
                        await ctx.send(f"⚠️ Could not restore roles for {member.name}: {e}")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to process backup file: {e}")
            return

        await ctx.send(f"✅ Restore complete. Processed {restored} members.")
        return

    # --- Standard or Dry Rollback from role_updates.log ---

    if not os.path.exists(update_log_path):
        await ctx.send("No log file found for rollback. (this will end well, won't it?)")
        return

    await ctx.send("Rollback initiated. This may take a while, perhaps get some espresso in the meantime?")

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

            member = guild.get_member(member_id)
            if not member:
                continue

            roles_to_add = [discord.utils.get(guild.roles, name=r) for r in remove_roles if discord.utils.get(guild.roles, name=r)]
            roles_to_remove = [discord.utils.get(guild.roles, name=r) for r in add_roles if discord.utils.get(guild.roles, name=r)]

            log_msg = f"Rollback for {member.name}: add {[r.name for r in roles_to_add]}, remove {[r.name for r in roles_to_remove]}"
            update_logger.info(f"{'[DRY ROLLBACK]' if is_dry_run else '[ROLLBACK]'} {log_msg}")
            print(f"[↩] {log_msg}")
            rollback_count += 1

            if not is_dry_run:
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)

    # --- Delete Roles Created by Mauve if needed ---
    deleted_roles = []
    if os.path.exists(role_creation_path):
        with open(role_creation_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(r".*\[CREATED_ROLE\] (\d+):(.+)", line)
                if match and match.group(1) == str(guild.id):
                    role_name = match.group(2)
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role:
                        try:
                            if not is_dry_run:
                                await role.delete(reason="Rollback of created role")
                            deleted_roles.append(role_name)
                        except Exception as e:
                            await ctx.send(f"Could not delete role `{role_name}`: {e}")

    # --- Final Reporting ---
    await ctx.send(f"Rollback {'test' if is_dry_run else 'complete'} — {rollback_count} member entries processed.")
    if deleted_roles:
        await ctx.send(f"Deleted roles: {', '.join(deleted_roles)}")

    try:
        with open(update_log_path, 'rb') as f:
            await ctx.send("Here's the updated log:", file=discord.File(f, filename='role_updates.log'))
    except Exception as e:
        await ctx.send(f"Couldn't upload the log for some reason: {e}")

# I was curious what servers the bot was in

@bot.command()
async def list(ctx):
    if ctx.author.id != 1191948659160518656:
        await ctx.send("Usage of this command is limited to StylisticallyCatgirl!")
        return

    server_list = "\n".join([f"{guild.name} (ID: {guild.id})" for guild in bot.guilds])
    await ctx.send(f"The bot is in the following servers:\n```{server_list}```")

# Makes sure that every role that is expected to be present is actually present

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
                title="I can't find these roles!",
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

# I'm not sure why I wrote this, but it was useful so it stays

@bot.command()
@commands.has_role("MauvePermissions")
async def create_missing_roles(ctx):
    guild = ctx.guild
    created_roles = []

    for legacy, (pronoun, color) in role_mappings.items():
        for role_name in [legacy, pronoun, color]:
            if not discord.utils.get(guild.roles, name=role_name):
                try:
                    await guild.create_role(name=role_name, reason="Auto-created from Mauve role mapping")
                    created_roles.append(role_name)
                    role_logger.info(f"[CREATED_ROLE] {guild.id}:{role_name}")
                except discord.Forbidden:
                    await ctx.send(f"I don't have the permissions to create' `{role_name}`")
                except Exception as e:
                    await ctx.send(f"I couldn't create' `{role_name}` ' for some reason': {e}")

    if created_roles:
        embed = discord.Embed(
            title="Created Missing Roles",
            description="\n".join(created_roles),
            color=discord.Color.purple()
        )
    else:
        embed = discord.Embed(
            title="All Roles Present",
            description="Everything is as it should be",
            color=discord.Color.purple()
        )

    await ctx.send(embed=embed)


# Everything below this is mostly just for testing
# Probably not such a hot idea to run these on servers you care about

@bot.command()
@commands.has_role("MauvePermissions")
async def assign_legacy_roles(ctx, mode: str = None):
    is_dry_run = mode == "dry"
    guild = ctx.guild
    all_members = [m for m in guild.members if not m.bot]


    if len(all_members) < 50:
        await ctx.send("I need more than 50 users present to run this command!")
        return

    selected_members = random.sample(all_members, 50)
    assigned_log = []

    update_logger.info(f"{'[DRY RUN]' if is_dry_run else '[UPDATE]'} [LEGACY_ASSIGN] started by {ctx.author} in guild '{guild.name}'")

    for member in selected_members:
        role_count = random.randint(1, min(5, len(legacy_roles)))
        chosen_role_names = random.sample(legacy_roles, role_count)

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
                    assigned_log[-1] += " Permission error"
                except Exception as e:
                    assigned_log[-1] += f" Error: {e}"

    if not assigned_log:
        await ctx.send("No roles were assigned.")
        return

    embed = discord.Embed(
        title="Legacy Role Assignment (Test run)" if is_dry_run else "Legacy Roles Assigned",
        description="\n".join(assigned_log[:10]) + ("\n... (truncated)" if len(assigned_log) > 10 else ""),
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

    try:
        with open(update_log_path, 'rb') as f:
            await ctx.send("Here's the full update log:", file=discord.File(f, filename='role_updates.log'))
    except Exception as e:
        await ctx.send(f"Could not upload the log: {e}")


@bot.command()
@commands.has_role("MauvePermissions")
async def clear_roles(ctx):

    # Single confirmation
    confirmation_message = await ctx.send(
        "Are you sure you want to remove all legacy, pronoun, and color roles from users?\nReact with ✅ to proceed or ❌ to cancel."
    )
    await confirmation_message.add_reaction("✅")
    await confirmation_message.add_reaction("❌")

    def check_reaction(reaction, user):
        return (
            user == ctx.author 
            and str(reaction.emoji) in ["✅", "❌"] 
            and reaction.message.id == confirmation_message.id
        )

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
        if str(reaction.emoji) != "✅":
            return await ctx.send("Aborting!")
    except asyncio.TimeoutError:
        return await ctx.send("Timeout!")

    # Role removal logic
    removed_count = 0
    for member in ctx.guild.members:
        roles_to_remove = []

        for legacy_name, (pronoun_name, color_name) in role_mappings.items():
            for role_name in [legacy_name, pronoun_name, color_name]:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                if role and role in member.roles:
                    roles_to_remove.append(role)

        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason="Mass role removal via clear_roles")
                removed_count += 1
            except discord.Forbidden:
                await ctx.send(f"Missing permissions to remove roles from {member.mention}.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to remove roles from {member.mention}: {e}")

    await ctx.send(f"Done! Removed all mapped roles from {removed_count} members.")

# I don't like doing math so I added this

@bot.command(name="count")
@commands.has_role("MauvePermissions")
async def count_legacy(ctx):
    guild = ctx.guild
    legacy_role_names = set(role_mappings.keys())
    legacy_roles = [role for role in guild.roles if role.name in legacy_role_names]
    legacy_member_count = 0

    for member in guild.members:
        if any(role in legacy_roles for role in member.roles):
            legacy_member_count += 1

    await ctx.send(f"{legacy_member_count} users have a legacy role.")



# Run the bot
bot.run(TOKEN, log_handler=handler)
