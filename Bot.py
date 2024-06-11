import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io

# Initialize the bot with the desired intents
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree  # For handling slash commands

polls = {}

# List of emoji options (1️⃣, 2️⃣, 3️⃣, ...)
emoji_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

# Channel ID to send poll creation notifications (replace with your channel ID)
poll_channel_id = "YOUR CHANNEL ID"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await sync_commands()

async def sync_commands():
    await bot.tree.sync()  # Sync slash commands with Discord

# Define the slash command for poll creation
@tree.command(name="poll", description="Create a poll with up to 10 options.")
@discord.app_commands.describe(
    question="The poll question.",
    option1="First option.",
    option2="Second option.",
    option3="Third option (optional).",
    option4="Fourth option (optional).",
    option5="Fifth option (optional).",
    option6="Sixth option (optional).",
    option7="Seventh option (optional).",
    option8="Eighth option (optional).",
    option9="Ninth option (optional).",
    option10="Tenth option (optional)."
)
async def poll(
    interaction: discord.Interaction,
    question: str,
    option1: str,
    option2: str,
    option3: str = None,
    option4: str = None,
    option5: str = None,
    option6: str = None,
    option7: str = None,
    option8: str = None,
    option9: str = None,
    option10: str = None
):
    options = [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10]
    options = [opt for opt in options if opt is not None]

    if len(options) < 2:
        await interaction.response.send_message('You need at least two options to create a poll.', ephemeral=True)
        return
    if len(options) > 10:
        await interaction.response.send_message('You can only create polls with up to 10 options.', ephemeral=True)
        return

    # Create an embed for the poll
    embed = discord.Embed(title="Poll", description=f"**{question}**", color=0x00ff00)
    for i, option in enumerate(options):
        embed.add_field(name=f"{emoji_list[i]} {option}", value='\u200b', inline=False)

    # Send the embedded poll message
    await interaction.response.send_message(embed=embed)

    # Get the original response message object to add reactions
    poll_message = await interaction.original_response()

    # Add reactions to the poll message
    for i in range(len(options)):
        await poll_message.add_reaction(emoji_list[i])

    # Save the poll details in the polls dictionary
    polls[poll_message.id] = {
        'question': question,
        'options': options,
        'message_id': poll_message.id,
        'channel_id': interaction.channel_id,
        'guild_id': interaction.guild_id
    }

    # Send poll creation notification to the specified channel
    poll_channel = bot.get_channel(poll_channel_id)
    if poll_channel:
        await poll_channel.send(f'Poll created with ID: {poll_message.id} in {interaction.channel.mention}')

# Define the !pollresults command with an optional channel argument
@bot.command()
async def pollresults(ctx, poll_id: int, channel_name: str = None):
    try:
        poll_data = polls.get(poll_id)

        if not poll_data:
            await ctx.send('Poll not found.')
            return

        # Fetch the poll message
        poll_channel = bot.get_channel(poll_data['channel_id'])
        message = await poll_channel.fetch_message(poll_data['message_id'])

        # Collecting the votes
        results = {}
        for reaction in message.reactions:
            if reaction.emoji in emoji_list:
                index = emoji_list.index(reaction.emoji)
                results[poll_data['options'][index]] = reaction.count - 1  # Subtracting the bot's own reaction

        # Prepare results for display
        labels = list(results.keys())
        sizes = list(results.values())

        # Create a pie chart
        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title(f"Poll Results: {poll_data['question']}")
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Save the plot to a buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close()

        # Determine the target channel
        if channel_name:
            target_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            if target_channel is None:
                await ctx.send(f"Channel '{channel_name}' not found.")
                return
        else:
            target_channel = ctx.channel

        # Additionally, send the text results
        result_text = f"**Results for poll: {poll_data['question']}**\n\n"
        for option, count in results.items():
            result_text += f"{option}: {count} votes\n"

        await target_channel.send(result_text)
        await target_channel.send(file=discord.File(fp=buffer, filename='poll_results.png'))

    except Exception as e:
        await ctx.send(f'An error occurred while retrieving the poll results: {e}')


# Running the bot
bot.run('YOUR DISCORD BOT TOKEN')
