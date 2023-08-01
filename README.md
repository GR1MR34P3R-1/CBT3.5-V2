# CBT3.5 - ChatBotTurbo3.5-V2 🚀

Welcome to **CBT3.5-V2**, the ultimate ChatBot powered by GPT-3.5 Turbo! 🤖

## Features 🔥

- AI-powered responses in the "ask-anything" channel
- Automatic cleanup of non "ask-anything" channels
- Message logging to a SQLite database
- Exporting logs to a text file for future reference

## Requirements 📋

Before running CBT3.5, make sure you have the following dependencies installed:

- `discord` (version 1.7.3 or later)
- `openai` (version 0.27.0 or later)
- `pytz` (version 2021.1 or later)
- `sqlite3`

## Installation 🛠️

1. Clone this repository to your local machine.
2. Install the required dependencies using pip:

```bash
pip install discord openai pytz
```
3. Create a config.ini file with your Discord bot token and OpenAI API key, and specify the necessary configuration options as shown below:

``` 
[Bot]
token = YOUR_DISCORD_BOT_TOKEN
api_key = YOUR_OPENAI_API_KEY
cleanup_duration = 60
```
4. Run the bot:
```
python3 main.py
```
## Usage 💬

- Make sure CBT3.5 is running and has been added to your Discord server.
- Create a channel named "ask-anything" where users can interact with the AI.
- Users with both the "Special Access" and "Verified" roles can ask questions and receive AI-generated responses in the "ask-anything" channel.
- The bot will automatically delete its own messages after 2 minutes to keep the channel clean.
- If a user lacks the required roles, the bot will inform them and delete their message instantly.

## Customization 🎨

- You can customize CBT3.5's behavior by modifying the code in the bot.py file. Feel free to experiment and add new features!

## Logging and Exporting 📝

- CBT3.5 logs all user messages, commands, and bot responses to a SQLite database. Additionally, the bot exports these logs to a text file named loggeddata.txt for easy reference.

## License 📜

This program is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute it as per the terms of the license.📄

## Have A Good Day!!

🌟 Have fun exploring the capabilities of CBT3.5 and enjoy interacting with the Discord bot! If you have any questions or need assistance, don't hesitate to reach out. 😊
