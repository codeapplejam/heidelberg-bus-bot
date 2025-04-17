# Heidelberg Bus Driver Navigation Bot - Implementation Guide

This guide will walk you through setting up and using the Telegram bot for bus drivers in Heidelberg. The bot helps you navigate your bus routes, check your work schedule, and get turn-by-turn directions between stations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up Your Telegram Bot](#setting-up-your-telegram-bot)
3. [Installation and Configuration](#installation-and-configuration)
4. [Preparing Your Data](#preparing-your-data)
5. [Running the Bot](#running-the-bot)
6. [Using the Bot](#using-the-bot)
7. [Deployment Options](#deployment-options)
8. [Customization](#customization)

## Prerequisites

- Basic knowledge of command line operations
- A Telegram account
- Python 3.7 or higher installed on your computer
- Your work schedule in digital format
- Information about bus routes and stations

## Setting Up Your Telegram Bot

### Step 1: Create a New Bot with BotFather

1. Open Telegram and search for "@BotFather"
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the prompts to name your bot
   - First, provide a display name (e.g., "Heidelberg Bus Navigator")
   - Then, provide a username that must end with "bot" (e.g., "HeidelbergBusBot")
4. BotFather will provide you with a token - **save this token securely** as it's needed to control your bot

### Step 2: Configure Bot Settings

1. Set a profile picture with `/setuserpic` (optional)
2. Set a description with `/setdescription` (e.g., "Navigation assistant for Heidelberg bus drivers")
3. Set commands with `/setcommands` to define the commands your bot will respond to:

```
start - Start the bot
help - Show help message
schedule - Show today's work schedule
routes - Show all available bus routes
route - Show details for a specific bus line
navigate - Get navigation instructions
upload - Upload a new work schedule
```

## Installation and Configuration

### Step 1: Download the Bot Code

Download the `heidelberg_bus_bot.py` file to your computer.

### Step 2: Set Up a Virtual Environment

```bash
# Create a new directory for your bot
mkdir heidelberg_bus_bot
cd heidelberg_bus_bot

# Copy the bot code into this directory
# (Place heidelberg_bus_bot.py in this folder)

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Required Libraries

Create a file named `requirements.txt` with the following content:

```
python-telegram-bot==13.15
python-dotenv==1.0.0
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

### Step 4: Create Environment Variables File

Create a file named `.env` in the same directory as your bot code with the following content:

```
TELEGRAM_TOKEN=your_telegram_bot_token_here
```

Replace `your_telegram_bot_token_here` with the token you received from BotFather.

## Preparing Your Data

### Bus Routes Data

The bot comes with sample bus route data for Heidelberg. To customize it with your actual routes:

1. Open `heidelberg_bus_bot.py` in a text editor
2. Find the `BUS_ROUTES` dictionary near the top of the file
3. Modify the routes, stations, and coordinates to match your actual bus routes

Example format:

```python
BUS_ROUTES = {
    "31": {
        "name": "Route 31",
        "stations": [
            {"name": "Hauptbahnhof", "coords": [49.4037, 8.6756]},
            {"name": "Bismarckplatz", "coords": [49.4094, 8.6947]},
            # Add more stations...
        ]
    },
    # Add more routes...
}
```

### Work Schedule Data

You can upload your work schedule in two ways:

1. **CSV Upload**: Prepare a CSV file with your schedule in the following format:

```
date,umlauf,start_time,end_time,routes
2025-04-17,U1,08:00,12:00,"31,32"
2025-04-17,U2,13:00,17:00,33
2025-04-18,U3,09:00,14:00,"32,33"
```

2. **Direct Code Modification**: Edit the `WORK_SCHEDULES` dictionary in the code:

```python
WORK_SCHEDULES = {
    "driver123": {  # This is your driver ID
        "2025-04-17": [
            {"umlauf": "U1", "start_time": "08:00", "end_time": "12:00", "routes": ["31", "32"]},
            # Add more shifts...
        ],
        # Add more days...
    }
}
```

## Running the Bot

To start the bot, run the following command in your terminal:

```bash
# Make sure your virtual environment is activated
python heidelberg_bus_bot.py
```

The bot will start and connect to Telegram. You should see a message like:

```
Bot started. Press Ctrl+C to stop.
```

## Using the Bot

### Basic Commands

- `/start` - Start the bot and get a welcome message
- `/help` - Show available commands and how to use them
- `/schedule` - Show your work schedule for today
- `/schedule YYYY-MM-DD` - Show your work schedule for a specific date
- `/routes` - Show all available bus routes
- `/route NUMBER` - Show details for a specific bus line (e.g., `/route 31`)
- `/navigate LINE FROM TO` - Get navigation instructions (e.g., `/navigate 31 Hauptbahnhof Bismarckplatz`)
- `/upload` - Get instructions for uploading a new work schedule

### Navigation Features

1. **Viewing Your Schedule**:
   - Use `/schedule` to see today's shifts
   - Each shift shows the Umlauf number, time, and assigned routes
   - Click on route buttons to see route details

2. **Exploring Routes**:
   - Use `/routes` to see all available bus lines
   - Click on a route to see all stations
   - Use `/route NUMBER` to directly view a specific route

3. **Getting Directions**:
   - From a route view, click on navigation buttons to get directions between stations
   - Use `/navigate LINE FROM TO` for custom navigation between any stations
   - Navigation includes turn-by-turn directions and map links

4. **Updating Your Schedule**:
   - Use `/upload` to get instructions for uploading a new schedule
   - Send a CSV file as described in the format above
   - The bot will process the file and update your schedule

## Deployment Options

For the bot to be available 24/7, you'll need to deploy it to a server or hosting service.

### Option 1: Deploy on PythonAnywhere (Free)

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Upload your bot files (`heidelberg_bus_bot.py`, `requirements.txt`, `.env`)
3. Open a Bash console and create a virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.8 mybot
   pip install -r requirements.txt
   ```
4. Set up a scheduled task to keep your bot running:
   - Go to the "Tasks" tab
   - Add a new task that runs every day
   - Command: `cd /home/yourusername/heidelberg_bus_bot && python heidelberg_bus_bot.py`

### Option 2: Deploy on Render (Free)

1. Sign up for a free account at [Render](https://render.com/)
2. Create a new Web Service
3. Connect to your GitHub repository (you'll need to push your code to GitHub first)
4. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python heidelberg_bus_bot.py`
   - Add the environment variable: `TELEGRAM_TOKEN`

### Option 3: Run on a Raspberry Pi

If you have a Raspberry Pi, you can run your bot 24/7 at home:

1. Install Python on your Raspberry Pi
2. Copy your bot files to the Pi
3. Install dependencies: `pip install -r requirements.txt`
4. Set up a service to keep the bot running:
   ```bash
   sudo nano /etc/systemd/system/telegrambot.service
   ```
   
   Add the following content:
   ```
   [Unit]
   Description=Telegram Bot Service
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/heidelberg_bus_bot
   ExecStart=/usr/bin/python3 /home/pi/heidelberg_bus_bot/heidelberg_bus_bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start the service:
   ```bash
   sudo systemctl enable telegrambot.service
   sudo systemctl start telegrambot.service
   ```

## Customization

### Adding More Bus Routes

To add more bus routes, edit the `BUS_ROUTES` dictionary in the code:

```python
BUS_ROUTES = {
    # Existing routes...
    
    "34": {
        "name": "Route 34",
        "stations": [
            {"name": "New Station 1", "coords": [49.4037, 8.6756]},
            {"name": "New Station 2", "coords": [49.4094, 8.6947]},
            # Add more stations...
        ]
    }
}
```

### Improving Navigation

For better turn-by-turn navigation, you can enhance the `get_directions` function to use a navigation API like OpenStreetMap's Nominatim or Google Maps Directions API.

Example improvement (requires additional libraries):

```python
import requests

def get_directions(from_station, to_station, from_coords, to_coords):
    """
    Get directions between two stations using OpenStreetMap
    """
    # This is a simplified example - you would need to implement proper API calls
    url = f"https://router.project-osrm.org/route/v1/driving/{from_coords[1]},{from_coords[0]};{to_coords[1]},{to_coords[0]}?overview=false&steps=true"
    
    response = requests.get(url)
    data = response.json()
    
    directions = []
    if data["code"] == "Ok":
        for step in data["routes"][0]["legs"][0]["steps"]:
            directions.append(step["maneuver"]["instruction"])
    
    return "\n".join(directions) if directions else f"Drive from {from_station} to {to_station}. Follow the main road."
```

### Supporting Multiple Languages

To support multiple languages, you can implement a language selection system:

1. Add a `/language` command to switch between languages
2. Create dictionaries for each supported language
3. Store the user's language preference

This would be particularly useful if you want to share the bot with drivers who prefer different languages.

---

This guide provides everything you need to set up, configure, and use the Heidelberg Bus Driver Navigation Bot. If you encounter any issues or have questions, feel free to reach out for assistance.
