import os
import logging
import json
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sample data structure for bus routes
# In a real implementation, this would be loaded from a database or file
BUS_ROUTES = {
    "31": {
        "name": "Route 31",
        "stations": [
            {"name": "Hauptbahnhof", "coords": [49.4037, 8.6756]},
            {"name": "Bismarckplatz", "coords": [49.4094, 8.6947]},
            {"name": "Universitätsplatz", "coords": [49.4119, 8.7089]},
            {"name": "Technologiepark", "coords": [49.4178, 8.6756]}
        ]
    },
    "32": {
        "name": "Route 32",
        "stations": [
            {"name": "Betriebshof", "coords": [49.4178, 8.6756]},
            {"name": "Neuenheimer Feld", "coords": [49.4178, 8.6756]},
            {"name": "Universitätsklinikum", "coords": [49.4178, 8.6756]},
            {"name": "Hans-Thoma-Platz", "coords": [49.4178, 8.6756]}
        ]
    },
    "33": {
        "name": "Route 33",
        "stations": [
            {"name": "Bismarckplatz", "coords": [49.4094, 8.6947]},
            {"name": "Handschuhsheim", "coords": [49.4178, 8.6756]},
            {"name": "Dossenheim", "coords": [49.4178, 8.6756]},
            {"name": "Schriesheim", "coords": [49.4178, 8.6756]}
        ]
    }
}

# Sample data structure for work schedules
# In a real implementation, this would be loaded from a database or file
WORK_SCHEDULES = {
    "driver123": {
        "2025-04-17": [
            {"umlauf": "U1", "start_time": "08:00", "end_time": "12:00", "routes": ["31", "32"]},
            {"umlauf": "U2", "start_time": "13:00", "end_time": "17:00", "routes": ["33"]}
        ],
        "2025-04-18": [
            {"umlauf": "U3", "start_time": "09:00", "end_time": "14:00", "routes": ["32", "33"]}
        ]
    }
}

def get_directions(from_station, to_station):
    """
    Get directions between two stations
    In a real implementation, this would use a navigation API or algorithm
    """
    # This is a placeholder - in a real implementation, you would use
    # OpenStreetMap or another navigation service to get actual directions
    return f"Drive from {from_station} to {to_station}. Follow the main road."

def get_map_link(coords):
    """
    Generate a Google Maps link for the given coordinates
    """
    lat, lon = coords
    return f"https://www.google.com/maps?q={lat},{lon}"

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(
        f'Hallo {user.first_name}! Ich bin dein Bus-Navigations-Bot für Heidelberg. '
        f'Verwende /help, um zu sehen, wie ich dir helfen kann.'
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    commands = """
Verfügbare Befehle:
/start - Starte den Bot
/help - Zeige diese Hilfenachricht
/schedule - Zeige deinen Arbeitsplan für heute
/schedule YYYY-MM-DD - Zeige deinen Arbeitsplan für ein bestimmtes Datum
/routes - Zeige alle verfügbaren Buslinien
/route NUMMER - Zeige Details zu einer bestimmten Buslinie
/navigate LINIE STARTSTATION ZIELSTATION - Erhalte Navigationsanweisungen
/upload - Lade einen neuen Arbeitsplan hoch (Anhang an diese Nachricht)
"""
    update.message.reply_text(commands)

def schedule_command(update: Update, context: CallbackContext) -> None:
    """Show work schedule for a specific date or today."""
    # In a real implementation, you would identify the user and retrieve their schedule
    driver_id = "driver123"  # Placeholder - would be determined by user authentication
    
    # Determine which date to show
    if context.args and len(context.args) > 0:
        try:
            date_str = context.args[0]
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            update.message.reply_text(
                'Ungültiges Datumsformat. Bitte verwende YYYY-MM-DD.'
            )
            return
    else:
        # Use today's date if none specified
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Get schedule for the specified date
    if driver_id in WORK_SCHEDULES and date_str in WORK_SCHEDULES[driver_id]:
        schedule = WORK_SCHEDULES[driver_id][date_str]
        
        response = f"Arbeitsplan für {date_str}:\n\n"
        for shift in schedule:
            routes_str = ", ".join([f"Linie {r}" for r in shift["routes"]])
            response += f"Umlauf: {shift['umlauf']}\n"
            response += f"Zeit: {shift['start_time']} - {shift['end_time']}\n"
            response += f"Linien: {routes_str}\n\n"
            
            # Add buttons for each route
            keyboard = []
            for route in shift["routes"]:
                keyboard.append([InlineKeyboardButton(
                    f"Details Linie {route}", 
                    callback_data=f"route_{route}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
        update.message.reply_text(response, reply_markup=reply_markup)
    else:
        update.message.reply_text(
            f'Kein Arbeitsplan für {date_str} gefunden.'
        )

def routes_command(update: Update, context: CallbackContext) -> None:
    """Show all available bus routes."""
    response = "Verfügbare Buslinien:\n\n"
    
    keyboard = []
    for route_id, route_data in BUS_ROUTES.items():
        response += f"Linie {route_id}: {route_data['name']}\n"
        keyboard.append([InlineKeyboardButton(
            f"Details Linie {route_id}", 
            callback_data=f"route_{route_id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(response, reply_markup=reply_markup)

def route_command(update: Update, context: CallbackContext) -> None:
    """Show details for a specific bus route."""
    if not context.args or len(context.args) == 0:
        update.message.reply_text(
            'Bitte gib eine Liniennummer an. Beispiel: /route 31'
        )
        return
    
    route_id = context.args[0]
    if route_id in BUS_ROUTES:
        route_data = BUS_ROUTES[route_id]
        
        response = f"Details für Linie {route_id} ({route_data['name']}):\n\n"
        response += "Stationen:\n"
        
        for i, station in enumerate(route_data['stations']):
            response += f"{i+1}. {station['name']}\n"
        
        # Add navigation buttons between stations
        keyboard = []
        for i in range(len(route_data['stations']) - 1):
            from_station = route_data['stations'][i]['name']
            to_station = route_data['stations'][i+1]['name']
            keyboard.append([InlineKeyboardButton(
                f"Navigation: {from_station} → {to_station}", 
                callback_data=f"nav_{route_id}_{i}_{i+1}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(response, reply_markup=reply_markup)
    else:
        update.message.reply_text(
            f'Buslinie {route_id} nicht gefunden.'
        )

def navigate_command(update: Update, context: CallbackContext) -> None:
    """Provide navigation instructions between stations on a route."""
    if not context.args or len(context.args) < 3:
        update.message.reply_text(
            'Bitte gib eine Liniennummer, Start- und Zielstation an. '
            'Beispiel: /navigate 31 Hauptbahnhof Bismarckplatz'
        )
        return
    
    route_id = context.args[0]
    from_station_name = context.args[1]
    to_station_name = " ".join(context.args[2:])
    
    if route_id in BUS_ROUTES:
        route_data = BUS_ROUTES[route_id]
        
        # Find station indices
        from_idx = -1
        to_idx = -1
        for i, station in enumerate(route_data['stations']):
            if station['name'].lower() == from_station_name.lower():
                from_idx = i
            if station['name'].lower() == to_station_name.lower():
                to_idx = i
        
        if from_idx == -1 or to_idx == -1:
            update.message.reply_text(
                'Eine oder beide Stationen wurden nicht gefunden. '
                'Bitte überprüfe die Stationsnamen.'
            )
            return
        
        # Generate navigation instructions
        response = f"Navigation für Linie {route_id} von {from_station_name} nach {to_station_name}:\n\n"
        
        # In a real implementation, you would use a navigation API to get turn-by-turn directions
        # This is a simplified example
        if from_idx < to_idx:
            # Forward direction
            for i in range(from_idx, to_idx):
                current = route_data['stations'][i]
                next_station = route_data['stations'][i+1]
                response += f"{i+1}. Von {current['name']} nach {next_station['name']}\n"
                response += f"   {get_directions(current['name'], next_station['name'])}\n"
                
                # Add map link
                map_link = get_map_link(next_station['coords'])
                response += f"   [Karte]({map_link})\n\n"
        else:
            # Reverse direction
            for i in range(from_idx, to_idx, -1):
                current = route_data['stations'][i]
                next_station = route_data['stations'][i-1]
                response += f"{from_idx-i+1}. Von {current['name']} nach {next_station['name']}\n"
                response += f"   {get_directions(current['name'], next_station['name'])}\n"
                
                # Add map link
                map_link = get_map_link(next_station['coords'])
                response += f"   [Karte]({map_link})\n\n"
        
        update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(
            f'Buslinie {route_id} nicht gefunden.'
        )

def upload_command(update: Update, context: CallbackContext) -> None:
    """Instruct the user how to upload a new work schedule."""
    update.message.reply_text(
        'Um einen neuen Arbeitsplan hochzuladen, sende mir eine CSV-Datei als Anhang '
        'mit dem folgenden Format:\n\n'
        'date,umlauf,start_time,end_time,routes\n'
        '2025-04-17,U1,08:00,12:00,"31,32"\n'
        '2025-04-17,U2,13:00,17:00,33\n'
        '2025-04-18,U3,09:00,14:00,"32,33"\n\n'
        'Sende die Datei als Antwort auf diese Nachricht.'
    )

def handle_document(update: Update, context: CallbackContext) -> None:
    """Handle uploaded documents (CSV files for work schedules)."""
    # Check if the message has a document
    if update.message.document:
        document = update.message.document
        
        # Check if it's a CSV file
        if document.file_name.endswith('.csv'):
            # Download the file
            file = context.bot.get_file(document.file_id)
            file_path = f"temp_{document.file_name}"
            file.download(file_path)
            
            try:
                # Process the CSV file
                process_schedule_csv(file_path, "driver123")  # In a real implementation, use actual driver ID
                update.message.reply_text(
                    'Arbeitsplan erfolgreich aktualisiert!'
                )
            except Exception as e:
                update.message.reply_text(
                    f'Fehler beim Verarbeiten der Datei: {str(e)}'
                )
            finally:
                # Clean up the temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            update.message.reply_text(
                'Bitte lade eine CSV-Datei hoch.'
            )

def process_schedule_csv(file_path, driver_id):
    """
    Process a CSV file containing work schedule information
    In a real implementation, this would update a database
    """
    # Initialize schedule dictionary if it doesn't exist
    if driver_id not in WORK_SCHEDULES:
        WORK_SCHEDULES[driver_id] = {}
    
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date = row['date']
            umlauf = row['umlauf']
            start_time = row['start_time']
            end_time = row['end_time']
            routes = row['routes'].split(',')
            
            # Add to schedule
            if date not in WORK_SCHEDULES[driver_id]:
                WORK_SCHEDULES[driver_id][date] = []
            
            WORK_SCHEDULES[driver_id][date].append({
                "umlauf": umlauf,
                "start_time": start_time,
                "end_time": end_time,
                "routes": routes
            })

def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data.startswith("route_"):
        # Route details button
        route_id = data.split("_")[1]
        if route_id in BUS_ROUTES:
            route_data = BUS_ROUTES[route_id]
            
            response = f"Details für Linie {route_id} ({route_data['name']}):\n\n"
            response += "Stationen:\n"
            
            for i, station in enumerate(route_data['stations']):
                response += f"{i+1}. {station['name']}\n"
            
            # Add navigation buttons between stations
            keyboard = []
            for i in range(len(route_data['stations']) - 1):
                from_station = route_data['stations'][i]['name']
                to_station = route_data['stations'][i+1]['name']
                keyboard.append([InlineKeyboardButton(
                    f"Navigation: {from_station} → {to_station}", 
                    callback_data=f"nav_{route_id}_{i}_{i+1}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(response, reply_markup=reply_markup)
        else:
            query.edit_message_text(f'Buslinie {route_id} nicht gefunden.')
    
    elif data.startswith("nav_"):
        # Navigation button
        parts = data.split("_")
        route_id = parts[1]
        from_idx = int(parts[2])
        to_idx = int(parts[3])
        
        if route_id in BUS_ROUTES:
            route_data = BUS_ROUTES[route_id]
            
            from_station = route_data['stations'][from_idx]
            to_station = route_data['stations'][to_idx]
            
            response = f"Navigation für Linie {route_id} von {from_station['name']} nach {to_station['name']}:\n\n"
            response += f"{get_directions(from_station['name'], to_station['name'])}\n\n"
            
            # Add map link
            map_link = get_map_link(to_station['coords'])
            response += f"[Karte öffnen]({map_link})"
            
            query.edit_message_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            query.edit_message_text(f'Buslinie {route_id} nicht gefunden.')

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(os.getenv('TELEGRAM_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("schedule", schedule_command))
    dispatcher.add_handler(CommandHandler("routes", routes_command))
    dispatcher.add_handler(CommandHandler("route", route_command))
    dispatcher.add_handler(CommandHandler("navigate", navigate_command))
    dispatcher.add_handler(CommandHandler("upload", upload_command))
    
    # Register callback query handler for buttons
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    
    # Register message handlers
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))

    # Start the Bot
    updater.start_polling()
    
    # Log that the bot has started
    logger.info("Bot started. Press Ctrl+C to stop.")
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
