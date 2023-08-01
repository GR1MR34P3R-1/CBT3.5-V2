import discord
from discord.ext import commands
import configparser
import openai
import asyncio
import sqlite3
import pytz
from datetime import datetime

# Read config.ini
config = configparser.ConfigParser()
config.read('config.ini')

token = config['Bot']['token']
api_key = config['Bot']['api_key']  # Read API key from the [Bot] section
cleanup_duration = int(config['Bot']['cleanup_duration'])

# Create an instance of the commands.Bot class
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize the OpenAI API
openai.api_key = api_key

# Create a connection to the database
db_connection = sqlite3.connect('database.db')

# Create a cursor object to execute SQL queries
db_cursor = db_connection.cursor()

# Create the tables if they don't exist
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS channel_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER,
        channel_name TEXT,
        guild_id INTEGER,
        guild_name TEXT,
        author_id INTEGER,
        author_name TEXT,
        content TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS command_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        guild_name TEXT,
        channel_id INTEGER,
        channel_name TEXT,
        author_id INTEGER,
        author_name TEXT,
        command TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Commit the changes to the database
db_connection.commit()

# Define a dictionary to cache generated responses
response_cache = {}


# Define a function to generate a response using ChatGPT 3.5 Turbo
async def generate_response(user_message, bot_user, bot_channel):
    model_prompt = f"User: {user_message.content}\nAI: "
    cache_key = model_prompt + str(user_message.author.id)

    if cache_key in response_cache:
        generated_text = response_cache[cache_key]
    else:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=model_prompt,
            max_tokens=100,
            temperature=0.7,
            n=1,
            stop=None,
            user=str(user_message.author.id),
        )
        generated_text = response.choices[0].text.strip()

        response_cache[cache_key] = generated_text

    bot_response = generated_text + ' AI: '

    # Log bot response
    log_message(bot_user, bot_channel, bot_response)

    return bot_response


# Function to log messages to the database and export logs to a text file
def log_message(author, channel, content):
    author_id = author.id
    author_name = author.name

    if author == bot.user:
        author_id = bot.user.id
        author_name = bot.user.name

    timestamp = datetime.now(pytz.timezone('America/Phoenix'))

    db_cursor.execute(
        '''
        INSERT INTO channel_logs (
            channel_id, channel_name, guild_id, guild_name,
            author_id, author_name, content, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        channel.id, channel.name,
        channel.guild.id, channel.guild.name,
        author_id, author_name,
        content, timestamp
    ))

    # Commit the changes to the database
    db_connection.commit()

    # Export logs to a text file
    export_logs()


# Function to export logs to a text file
def export_logs():
    db_cursor.execute('SELECT * FROM channel_logs')
    channel_logs = db_cursor.fetchall()
    with open('loggeddata.txt', 'w', encoding='utf-8') as file:
        file.write('Channel Logs:\n\n')
        for log in channel_logs:
            timestamp_str = log[8]
            timestamp = datetime.fromisoformat(timestamp_str)
            local_timestamp = timestamp.astimezone(pytz.timezone('America/Phoenix'))

            file.write(f'ID: {log[0]}\n')
            file.write(f'Channel: {log[2]} ({log[1]})\n')
            file.write(f'Guild: {log[4]} ({log[3]})\n')
            file.write(f'Author: {log[6]} ({log[5]})\n')
            file.write(f'Content: {log[7]}\n')
            file.write(f'Timestamp: {local_timestamp}\n\n')

    db_cursor.execute('SELECT * FROM command_logs')
    command_logs = db_cursor.fetchall()
    with open('loggeddata.txt', 'a', encoding='utf-8') as file:
        file.write('\n\nCommand Logs:\n\n')
        for log in command_logs:
            timestamp_str = log[8]
            timestamp = datetime.fromisoformat(timestamp_str)
            local_timestamp = timestamp.astimezone(pytz.timezone('America/Phoenix'))

            file.write(f'ID: {log[0]}\n')
            file.write(f'Guild: {log[2]} ({log[1]})\n')
            file.write(f'Channel: {log[4]} ({log[3]})\n')
            file.write(f'Author: {log[6]} ({log[5]})\n')
            file.write(f'Command: {log[7]}\n')
            file.write(f'Timestamp: {local_timestamp}\n\n')


# Event handler for the on_message event
@bot.event
async def on_message(message):
    if message.author == bot.user:
        # Delete bot messages after 2 minutes
        await asyncio.sleep(120)
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass
        return

    # Log message in the channel_logs table
    log_message(message.author, message.channel, message.content)

    if message.channel.name == "ask-anything":
        special_access_role = discord.utils.get(message.guild.roles, name="Special Access")
        verified_role = discord.utils.get(message.guild.roles, name="Verified")

        if special_access_role in message.author.roles and verified_role in message.author.roles:
            try:
                response = await generate_response(message, bot.user, message.channel)
                await message.channel.send(response)

                # Log bot response (handled in generate_response)

                # Delete user question after 1 minute
                await asyncio.sleep(60)
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass

                # Delete bot response after 2 minutes
                await asyncio.sleep(120)
                async for msg in message.channel.history(limit=200):
                    if (
                        msg.author == bot.user
                        and msg.reference is not None
                        and msg.reference.message_id == message.id
                    ):
                        try:
                            await msg.delete()
                        except discord.errors.NotFound:
                            pass
                        break
            except openai.Error as e:
                # Handle OpenAI API errors
                await message.channel.send(f"OpenAI API error: {str(e)}")
            except Exception as e:
                # Handle other errors
                await message.channel.send(f"An error occurred: {str(e)}")
        elif verified_role in message.author.roles:
            # User has only "Verified" role
            # Delete user message instantly
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass

            # Log access denial in the channel_logs table
            log_message(bot.user, message.channel, "You do not have the required role for special access.")

            # Send access denial message if not already sent
            error_sent = False
            async for msg in message.channel.history(limit=10):
                if (
                    msg.author == bot.user
                    and msg.content == "You do not have the required role for special access."
                ):
                    error_sent = True
                    break
            if not error_sent:
                await message.channel.send("You do not have the required role for special access.")
        else:
            # Log access denial in the channel_logs table
            log_message(bot.user, message.channel, "You do not have the required role for special access.")

            # Send access denial message if not already sent
            error_sent = False
            async for msg in message.channel.history(limit=10):
                if (
                    msg.author == bot.user
                    and msg.content == "You do not have the required role for special access."
                ):
                    error_sent = True
                    break
            if not error_sent:
                await message.channel.send("You do not have the required role for special access.")

    await bot.process_commands(message)


# Event handler for the on_command event
@bot.event
async def on_command(ctx):
    # Log the command in the command logs
    db_cursor.execute(
        '''
        INSERT INTO command_logs (
            guild_id, guild_name, channel_id, channel_name,
            author_id, author_name, command
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''',
        (
            ctx.guild.id, ctx.guild.name,
            ctx.channel.id, ctx.channel.name,
            ctx.author.id, ctx.author.name,
            ctx.message.content,
        ),
    )

    # Commit the changes to the database
    db_connection.commit()


# Event handler for the on_ready event
@bot.event
async def on_ready():
    print(f'Bot is ready. Connected to {len(bot.guilds)} server(s).')

    # Schedule the cleanup_channels function after the specified duration
    while True:
        await asyncio.sleep(cleanup_duration * 60)
        await cleanup_channels()


# Event handler for command-related errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore invalid commands silently
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument.")
    elif isinstance(error, openai.Error):
        await ctx.send(f"OpenAI API error: {str(error)}")
    else:
        error_message = f"An error occurred: {str(error)}"
        print(f"Error: {error_message}")
        await ctx.send("An error occurred while processing the command.")


## Cleanup function to delete all messages from non "ask-anything" text channels
async def cleanup_channels():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name != "ask-anything":  # Skip "ask-anything" channel
                # Start the purge process for all messages in the channel
                async for message in channel.history(limit=None):
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass

# Start the bot
bot.run(token)
