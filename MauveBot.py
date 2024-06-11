import discord
from discord.ext import commands
import asyncio
import logging

# Replace 'token here' with the token

TOKEN = 'token here'

# Just intents stuff (basically defines bot specific permissions)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

description = '''You probably shouldn't use this if you don't know what it does.

En masse role replacer made by catgirlandamoth (Sadie). Special thanks to Pea, Diane and all the rest on the rain discord for help!

If you're having issues with permissions did the bot create the "MauvePermissions" role? Have you assigned the role to yourself? If you're still having issues, consider rate limits or server size. Patience is a virue :3'''

# Sets up prefix "m;" description and intents

bot = commands.Bot(command_prefix='m;', description=description, intents=intents)

# Very advanced error handling

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRole) and "Role 'MauvePermissions' is required to run this command" in str(error):
        await ctx.send("I'm pretty sure you shouldn't be messing with this <3 (Lacking MauvePermissions role)")

# Automatically makes permissions role

@bot.event
async def on_ready():
    
    role_name = "MauvePermissions"
    
    for guild in bot.guilds:
        # Check if the role already exists
        role = discord.utils.get(guild.roles, name=role_name)
        
        if role:
            print('------')
            print(f"The role `{role_name}` already exists in guild `{guild.name}`.")
            print('------')
            print('Prelim checks complete, bot ready!')
        else:
            # Create the role
            try:
                await guild.create_role(name=role_name, reason="Role needed for specific permissions")
                print('------')
                print(f"The role `{role_name}` has been created in guild `{guild.name}`.")
                print('------')
                print('Prelim checks complete, bot ready!')
            except discord.Forbidden:
                print('------')
                print(f"I do not have permission to create roles in guild `{guild.name}`.")
                print('------')
                print('Permissions Error - Fix this before continuing!')
            except discord.HTTPException as e:
                print('------')
                print(f"An error occurred in guild `{guild.name}`: {str(e)}")
                print('------')
                print('Misc Error - Check terminal/logs and DM catgirlandamoth for help!')
    print('------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name="Lavender is such a pretty color"))

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Mauve')
handler = logging.FileHandler(filename='Mauve.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Basic ping command

@bot.command()
async def ping(ctx):
     await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# Role maps for index and update_role

role_mappings = {
    ".Ask": ("Ask", "color: Slate"),
    ".Name is pronoun": ("Name is pronoun", "color: Slate"),
    ".Any Pronouns": ("Any Pronouns", "color: Rose"),
    ".Not She/Her/Hers": ("Not She/Her/Hers", "color: Rose"),
    ".Not He/Him/His": ("Not He/Him/His", "color: Burnt Orange"),
    ".It/Its/Its": ("It/Its/Its", "color: Slate"),
    ".Fae/Faer/Faers": ("Fae/Faer/Faers", "color: Helio"),
    ".Ae/Aer": ("Ae/Aer", "color: Raspberry"),
    ".They/Them/Theirs": ("They/Them/Theirs", "color: Electric Purple"),
    ".He/Him/His": ("He/Him/His", "color: Blue"),
    ".She/Her/Hers": ("She/Her/Hers", "color: Bubblegum"),
    ".Vi/Ver/Vers": ("Vi/Ver/Vers", "color: Black"),
}

# Index command: Use caution on large servers. May lag and/or ratelimit

@bot.command()
@commands.has_role("MauvePermissions")
async def index(ctx):
    # This is the more efficent way to do it. - Jesse
    roles_to_check = list(role_mappings.keys())
    members_by_role = {role: [] for role in roles_to_check}
    # I don't actually remember why this works
    for member in ctx.guild.members:
        for role in member.roles:
            if role.name in roles_to_check:
                members_by_role[role.name].append(member.name)

    embed = discord.Embed(title="Members with legacy roles", color=discord.Color.purple())
    # Basically just lists all of the users with the roles in question and then also summerizes the number of users with those roles
    # Also a mostly harmless command to make sure this works at scale (god I hope it does)
    for role, members in members_by_role.items():
        total_members = len(members)
        if total_members > 0:
            embed.add_field(name=f"{role} ({total_members} members)", value='\n'.join(members), inline=False)
        else:
            embed.add_field(name=role, value="No members found with this role.", inline=False)

    await ctx.send(embed=embed)

# This is the actual replacement script

@bot.command()
@commands.has_role("MauvePermissions")
async def update_roles(ctx):
    # It's the litteral big red button, of course there's a confirmation
    confirmation_message = await ctx.send("You have 60 seconds to confirm this command. React with ✅ to confirm or ❌ to cancel.")

    await confirmation_message.add_reaction("✅")
    await confirmation_message.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
    # Cool, you confirmed the command! Now enjoy the wait.
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        if str(reaction.emoji) == "✅":
            await ctx.send("Confirmed. This will take a while. Progress is displayed in terminal")
            guild = ctx.guild
            for member in guild.members:
                for role_name, (new_role_name1, new_role_name2) in role_mappings.items():
                    role = discord.utils.get(guild.roles, name=role_name)
                    new_role1 = discord.utils.get(guild.roles, name=new_role_name1)
                    new_role2 = discord.utils.get(guild.roles, name=new_role_name2)
                    if role in member.roles:
                        await member.remove_roles(role)
                        await member.add_roles(new_role1, new_role2)
                        # prints to terminal
                        print(f"Updated roles for {member.name}: removed {role_name}, added {new_role_name1} and {new_role_name2}")
                        # prints to channel
                        embed = discord.Embed(
                                                title=f"Updated roles for {member.name}",
                                                description=f"Removed {role_name}, added {new_role_name1} and {new_role_name2}",
                                                color=discord.Color.purple()
                                                                                )
                        await ctx.send(embed=embed)
            await ctx.send("Roles have been updated successfully!")
        else:
            # I think my jokes are funny. Do you?
            await ctx.send("Canceled. You live to confirm another day :3")
    except asyncio.TimeoutError:
        # Every 60 seconds in New York a minute passes in Virginia
        await ctx.send("Canceled. Timeout.")

# Role names
roles_list = [
    ".Ask", "Ask", "color: Slate",
    ".Name is pronoun", "Name is pronoun", "color: Slate",
    ".Any Pronouns", "Any Pronouns", "color: Rose",
    ".Not She/Her/Hers", "Not She/Her/Hers", "color: Rose",
    ".Not He/Him/His", "Not He/Him/His", "color: Burnt Orange",
    ".It/Its/Its", "It/Its/Its", "color: Slate",
    ".Fae/Faer/Faers", "Fae/Faer/Faers", "color: Helio",
    ".Ae/Aer", "Ae/Aer", "color: Raspberry",
    ".They/Them/Theirs", "They/Them/Theirs", "color: Electric Purple",
    ".He/Him/His", "He/Him/His", "color: Blue",
    ".She/Her/Hers", "She/Her/Hers", "color: Bubblegum",
    ".Vi/Ver/Vers", "Vi/Ver/Vers", "color: Black"
]

@bot.command()
@commands.has_role("MauvePermissions")
async def spellcheck(ctx):
    guild = ctx.guild
    missing_roles = []
    
    for role_name in roles_list:
        # Check if the role already exists
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            missing_roles.append(role_name)
    
    if missing_roles:
        embed = discord.Embed(title="Missing Roles", color=discord.Colour.red())
        embed.add_field(name="Roles not found in the server", value="\n".join(missing_roles), inline=False)
        await ctx.send(embed=embed)
        await ctx.send("If anything is missing it's probably an issue with capitalization, or the role is spelled wrong")
    else:
        await ctx.send("All roles are present in the server!")

#pulls token from up top and should actually make the log handler work
bot.run(TOKEN, log_handler=handler)
