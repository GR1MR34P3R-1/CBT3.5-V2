# ChatBotTurbo3.5-V2 🚀

![Python Version](https://img.shields.io/badge/Python-3.6%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Welcome to **ChatBotTurbo3.5-V2**, the ultimate ChatBot powered by GPT-3.5 Turbo! 🤖

## Features 🔥

- AI-powered responses in the "ask-anything" channel
- Automatic cleanup of non "ask-anything" channels
- Message logging to a SQLite database
- Exporting logs to a text file for future reference

## Requirements 📋

Before running ChatBotTurbo3.5-V2, make sure you have the following dependencies installed:

- `discord` (version 1.7.3 or later)
- `openai` (version 0.27.0 or later)
- `pytz` (version 2021.1 or later)
- `sqlite3`

## Installation 🛠️

1. Clone this repository to your local machine.
2. Install the required dependencies using pip:

    ```pip install discord openai pytz```

3. Edit the config.ini file with your Discord bot token and OpenAI API key as shown below.

    **[Bot]
    token = YOUR_DISCORD_BOT_TOKEN
    api_key = YOUR_OPENAI_API_KEY
    cleanup_duration = 60**

4. Run the bot:

    ```python3 main.py```

## Usage 💬

- Make sure ChatBotTurbo3.5-V2 is running and has been added to your Discord server.
- Create a channel named "ask-anything" where users can interact with the AI.
- Users with both the "Special Access" and "Verified" roles can ask questions and receive AI-generated responses in the "ask-anything" channel.
- The bot will automatically delete its own messages after 2 minutes to keep the channel clean.
- If a user lacks the required roles, the bot will inform them and delete their message instantly.

## Customization 🎨

- You can customize ChatBotTurbo3.5-V2's behavior by modifying the code in the main.py file. Feel free to experiment and add new features!

## Logging and Exporting 📝

- ChatBotTurbo3.5-V2 logs all user messages, commands, and bot responses to a SQLite database. Additionally, the bot exports these logs to a text file named loggeddata.txt for easy reference.

## Error Handling and Troubleshooting 🚨

ChatBotTurbo3.5-V2 incorporates comprehensive error handling to ensure smooth operation and easy troubleshooting. Here are some common scenarios and how to address them:

- **OpenAI API Errors**: If you encounter errors related to the OpenAI API, such as rate limits exceeded or authentication issues, the bot will log these errors and inform users about the issue. You can check the bot's log files (`bot.log` and `openai.log`) for detailed error messages. To address API errors, ensure your OpenAI API key is correctly configured in the `config.ini` file and consider implementing retry logic or backoff strategies in your code.

- **Database Connection Issues**: If there are problems with the database connection, ChatBotTurbo3.5-V2 will log database-related errors and raise exceptions. Check the `database.log` file for more information on any database-related errors. Make sure the SQLite database file (`database.db`) is accessible, and the bot has the necessary permissions to read and write to it.

- **Discord API Errors**: Discord-related errors, such as permission issues or unexpected behavior, are logged by the bot in its log files. You can find more information in the `bot.log` file. Address Discord API errors by verifying the bot's permissions on your server and ensuring it has the required roles and privileges.

- **Customization and Code Errors**: If you make custom modifications to the bot's code and encounter issues, the bot will log errors in the `bot.log` file. Carefully review your code changes and refer to the log files for specific error messages. Proper code testing and debugging practices can help identify and resolve these issues.

By regularly checking the bot's log files and handling errors as they arise, you can maintain the stability and reliability of ChatBotTurbo3.5-V2. If you need assistance with specific error messages or troubleshooting, don't hesitate to seek help from the community or the bot's developers.

## License 📜

- This program is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute it as per the terms of the license.📄

## Have a Great Day! 🌟

- 🌟 Have fun exploring the capabilities of ChatBotTurbo3.5-V2 and enjoy interacting with the Discord bot! If you have any questions or need assistance, don't hesitate to reach out. 😊
