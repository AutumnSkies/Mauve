# Mauve

Mauve is a bot that does a few things related to roles.

1: By using the command m;index it spits out a list of every user with one of the 12 targeted roles, with a numbers summary appended.

2: By using the command m;replace it replaces all of the 12 targeted roles with their designated replacements

The bot also has a permissions role named "MauvePermissions" which is necessary to run all commands outside of m;ping

Mauve needs to be able to create and assign roles and manage users. Ensure the bots role "Mauve" is above the roles you are trying to edit

Please open a pull request if you make changes to this <3

---------

Requirements:

Latest version of Python
Discord.Py
Asyncio
Logging

---------

Instructions:

1. Download .Py and add secret to 'token here' keeping the little dash marks. Also swap roles to the ones you want changed in the code

2. Add Mauve to server with the link I sent you. (Or create your own app. Make sure intents are set up)

3. Create a dedicated channel to run Mauve in. The bot generates a significant amount of messages in chat, thus a one-time use mod only channel is likely a good plan

4. Run m;ping to test Mauve's connection to wherever you're running it. At this point Mauve should have created Mauve.log and is dumping the terminal to there. Don't open the file while the bot is writing to it or the logging breaks

5. Run m;index to check how many users and roles the bot will affect. Also a good litmus test on how the bot performs with the volume of users we're targeting

6. Run m;update_roles to actually change roles. This dumps all the changes to terminal and to chat in an embed. This will likely take a hot second depending on how good a thing you're running the bot on.

7. Make a cup of tea while you wait

8. The bot will send a message when it is done. Kick the bot and you're done.