import os
import io
import logging
import re
from datetime import datetime
from PIL import Image
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Driver, Schedule, BusRoute

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///schedules.db")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# OCR Configuration
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/4.00/tessdata")

# --------------------------
# Database Helper Functions
# --------------------------

def get_driver(telegram_id: int):
    """Retrieve driver from database"""
    with Session() as session:
        return session.query(Driver).filter_by(telegram_id=telegram_id).first()

def get_schedule(driver_id: int, date: datetime):
    """Get schedule for a specific date"""
    with Session() as session:
        return session.query(Schedule).filter(
            Schedule.driver_id == driver_id,
            Schedule.date == date.date()
        ).all()

def get_bus_route(route_number: str):
    """Get bus route details"""
    with Session() as session:
        return session.query(BusRoute).filter_by(route_number=route_number).first()

def get_all_routes():
    """Get all bus routes"""
    with Session() as session:
        return session.query(BusRoute).all()

# --------------------------
# Image Processing Functions
# --------------------------

def process_image(image):
    """Process image for OCR using OpenCV"""
    # Convert to OpenCV format
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # OCR processing
    return pytesseract.image_to_string(
        thresh,
        lang='deu+eng',
        config=f'--tessdata-dir "{TESSDATA_PREFIX}"'
    )

def parse_schedule_text(text: str, driver_id: int):
    """Parse OCR text into schedule data"""
    try:
        with Session() as session:
            # Example parsing pattern - customize based on your schedule format
            date_pattern = re.compile(r'Date:\s*(\d{4}-\d{2}-\d{2})')
            shift_pattern = re.compile(r'Umlauf:\s*(\w+)\s*Time:\s*(\d{2}:\d{2})-(\d{2}:\d{2})\s*Routes:\s*([\d,]+)')

            current_date = None
            for line in text.split('\n'):
                date_match = date_pattern.search(line)
                if date_match:
                    current_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    continue
                
                if current_date:
                    shift_match = shift_pattern.search(line)
                    if shift_match:
                        schedule = Schedule(
                            driver_id=driver_id,
                            date=current_date,
                            umlauf=shift_match.group(1),
                            start_time=datetime.strptime(shift_match.group(2), '%H:%M').time(),
                            end_time=datetime.strptime(shift_match.group(3), '%H:%M').time(),
                            routes=shift_match.group(4).split(',')
                        )
                        session.add(schedule)
            
            session.commit()
        return True
    except Exception as e:
        logger.error(f"Error parsing schedule: {str(e)}")
        return False

# --------------------------
# Telegram Command Handlers
# --------------------------

def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message"""
    user = update.effective_user
    update.message.reply_text(
        f'Hallo {user.first_name}! Ich bin dein Bus-Navigations-Bot für Heidelberg.\n'
        'Verwende /register um dich zu registrieren oder /help für Hilfe.'
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Show help message"""
    commands = """
Verfügbare Befehle:
/start - Starte den Bot
/help - Zeige diese Hilfe
/register - Als Fahrer registrieren
/schedule - Arbeitsplan für heute
/schedule [DATUM] - Arbeitsplan für bestimmtes Datum (YYYY-MM-DD)
/routes - Alle Buslinien anzeigen
/route [NUMMER] - Details einer Buslinie
/navigate [LINIE] [VON] [NACH] - Navigationsanweisungen
/upload - Arbeitsplan hochladen (Bild/PDF)
"""
    update.message.reply_text(commands)

def register_command(update: Update, context: CallbackContext) -> None:
    """Register new driver"""
    try:
        with Session() as session:
            driver = Driver(
                name=update.effective_user.full_name,
                telegram_id=update.effective_user.id
            )
            session.add(driver)
            session.commit()
        update.message.reply_text("Registrierung erfolgreich! 🎉")
    except Exception as e:
        update.message.reply_text("Registrierung fehlgeschlagen. Bitte Administrator kontaktieren.")

def schedule_command(update: Update, context: CallbackContext) -> None:
    """Show work schedule"""
    driver = get_driver(update.effective_user.id)
    if not driver:
        update.message.reply_text("Bitte zuerst mit /register registrieren.")
        return

    # Get date from arguments or use today
    try:
        date_str = context.args[0] if context.args else datetime.now().strftime('%Y-%m-%d')
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        update.message.reply_text("Ungültiges Datumsformat. Verwende YYYY-MM-DD.")
        return

    schedules = get_schedule(driver.id, target_date)
    if not schedules:
        update.message.reply_text(f"Kein Arbeitsplan für {date_str} gefunden.")
        return

    response = f"Arbeitsplan für {date_str}:\n\n"
    keyboard = []
    for schedule in schedules:
        response += f"Umlauf: {schedule.umlauf}\n"
        response += f"Zeit: {schedule.start_time} - {schedule.end_time}\n"
        response += f"Linien: {', '.join(schedule.routes)}\n\n"
        
        # Add buttons for each route
        for route in schedule.routes:
            keyboard.append([InlineKeyboardButton(
                f"Linie {route} Details",
                callback_data=f"route_{route}"
            )])

    update.message.reply_text(
        response,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def routes_command(update: Update, context: CallbackContext) -> None:
    """List all bus routes"""
    routes = get_all_routes()
    if not routes:
        update.message.reply_text("Keine Buslinien gefunden.")
        return

    keyboard = []
    response = "Verfügbare Buslinien:\n\n"
    for route in routes:
        response += f"Linie {route.route_number}: {route.name}\n"
        keyboard.append([InlineKeyboardButton(
            f"Linie {route.route_number}",
            callback_data=f"route_{route.route_number}"
        )])

    update.message.reply_text(response, reply_markup=InlineKeyboardMarkup(keyboard))

def route_command(update: Update, context: CallbackContext) -> None:
    """Show route details"""
    if not context.args:
        update.message.reply_text("Bitte Liniennummer angeben. Beispiel: /route 31")
        return

    route = get_bus_route(context.args[0])
    if not route:
        update.message.reply_text("Buslinie nicht gefunden.")
        return

    response = f"Linie {route.route_number}: {route.name}\n\nStationen:\n"
    for i, station in enumerate(route.stations):
        response += f"{i+1}. {station['name']}\n"

    # Navigation buttons
    keyboard = []
    for i in range(len(route.stations)-1):
        keyboard.append([InlineKeyboardButton(
            f"{route.stations[i]['name']} → {route.stations[i+1]['name']}",
            callback_data=f"nav_{route.route_number}_{i}_{i+1}"
        )])

    update.message.reply_text(
        response,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_document(update: Update, context: CallbackContext) -> None:
    """Process uploaded schedule documents"""
    driver = get_driver(update.effective_user.id)
    if not driver:
        update.message.reply_text("Bitte zuerst mit /register registrieren.")
        return

    file = context.bot.get_file(update.message.document.file_id)
    file_bytes = file.download_as_bytearray()

    try:
        # Process PDF files
        if update.message.document.mime_type == 'application/pdf':
            images = convert_from_bytes(bytes(file_bytes))
            text = "\n".join([process_image(img) for img in images])
        else:  # Process image files
            image = Image.open(io.BytesIO(file_bytes))
            text = process_image(image)

        if parse_schedule_text(text, driver.id):
            update.message.reply_text("Arbeitsplan erfolgreich aktualisiert! ✅")
        else:
            update.message.reply_text("Fehler beim Verarbeiten des Zeitplans. ❌")

    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        update.message.reply_text("Fehler beim Verarbeiten der Datei. Bitte Format überprüfen.")

# --------------------------
# Callback Handlers
# --------------------------

def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle inline keyboard button presses"""
    query = update.callback_query
    data = query.data

    if data.startswith("route_"):
        route_number = data.split("_")[1]
        route = get_bus_route(route_number)
        if route:
            response = f"Linie {route.route_number}: {route.name}\nStationen:\n"
            response += "\n".join([f"{i+1}. {s['name']}" for i, s in enumerate(route.stations)])
            query.edit_message_text(response)
        else:
            query.edit_message_text("Buslinie nicht gefunden.")

    elif data.startswith("nav_"):
        _, route_number, from_idx, to_idx = data.split("_")
        route = get_bus_route(route_number)
        if route:
            from_station = route.stations[int(from_idx)]
            to_station = route.stations[int(to_idx)]
            map_link = f"https://www.google.com/maps/dir/{from_station['coords'][0]},{from_station['coords'][1]}/{to_station['coords'][0]},{to_station['coords'][1]}"
            response = f"Navigation von {from_station['name']} nach {to_station['name']}:\n"
            response += f"Karte: {map_link}"
            query.edit_message_text(response)
        else:
            query.edit_message_text("Navigation nicht möglich.")

# --------------------------
# Main Application
# --------------------------

def main() -> None:
    """Start the bot"""
    updater = Updater(os.getenv('TELEGRAM_TOKEN'))
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("register", register_command))
    dispatcher.add_handler(CommandHandler("schedule", schedule_command))
    dispatcher.add_handler(CommandHandler("routes", routes_command))
    dispatcher.add_handler(CommandHandler("route", route_command))
    
    # Document handler
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))
    
    # Callback handler
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Start bot
    updater.start_polling()
    logger.info("Bot gestartet")
    updater.idle()

if __name__ == '__main__':
    main()
