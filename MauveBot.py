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

If you're having issues with permissions did you create and assign the "MauvePermissions" role? If you're still having issues, consider rate limits or server size. Patience is a virue :3'''

# Sets up prefix "m;" description and intents

bot = commands.Bot(command_prefix='m;', description=description, intents=intents)

# Sends a message in terminal to let us know the bot should be online, and thus accepting commands.
# Also sets presence. Lavender really is a pretty color.

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name="Lavender is such a pretty color"))

# Very advanced error handling

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRole) and "Role 'MauvePermissions' is required to run this command" in str(error):
        await ctx.send("I'm pretty sure you shouldn't be messing with this <3 (Lacking MauvePermissions role)")

# Configure logging - does this actually work? it's not writing to Mauve.log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Mauve')
handler = logging.FileHandler(filename='Mauve.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Basic ping command

@bot.command()
async def ping(ctx):
     await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

# It cannot be this fucking easy to do this
# Anyway, here we map out the roles we want gone and which ones replace them.
# Maybe move this to the top later?
# YOU WILL NEED TO CHANGE ALL OF THESE TO MATCH WHATEVER YOUR SERVER LOOKS LIKE
# Yes, it's tedious, sorry!

role_mappings = {
    "LegacyPronoun1": ("NewPronoun1", "color1"),
    "LegacyPronoun2": ("NewPronoun2", "color2"),
    "LegacyPronoun3": ("NewPronoun3", "color3"),
    "LegacyPronoun4": ("NewPronoun4", "color4"),
    "LegacyPronoun5": ("NewPronoun5", "color5"),
    "LegacyPronoun6": ("NewPronoun6", "color6"),
    "LegacyPronoun7": ("NewPronoun7", "color7"),
    "LegacyPronoun8": ("NewPronoun8", "color8"),
    "LegacyPronoun9": ("NewPronoun9", "color9"),
    "LegacyPronoun10": ("NewPronoun10", "color10"),
    "LegacyPronoun11": ("NewPronoun11", "color11"),
    "LegacyPronoun12": ("NewPronoun12", "color12"),
}

# Index command: Use caution on large servers. May lag and/or ratelimit
# I have no goddamn idea how this works on larger servers. Probably need to put in something that makes this bot ratelimit itself
# I think discord.py does rate limit internally though?. RUN INDEX COMMAND FIRST BEFORE PUSHING THE BIG RED BUTTON TO CHECK THIS

@bot.command()
# You'll see this a lot, it makes sure that the user has the proper permissions role. Without that role the command wont execute for god themselves
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

#pulls token from up top and should actually make the log handler work
bot.run(TOKEN, log_handler=handler)
