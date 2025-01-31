# main.py

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue,
)

from config.config import BotConfig
from database.database import Database
from handlers.user_handlers import UserCommandHandler
from handlers.admin_handlers import AdminCommandHandler
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logger(
    'kpg_malibu_bvb',
    'logs/bot.log',
    logging.INFO
)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates"""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    try:
        if update.message:
            await update.message.reply_text(
                "Sorry, an error occurred while processing your request."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}", exc_info=True)

class VolleyballBot:
    """Main bot class"""
    
    def __init__(self):
        """Initialize bot"""
        self.db = Database(f"{BotConfig.DATABASE['path']}{BotConfig.DATABASE['name']}")
        self.user_handler = UserCommandHandler(self.db, logger)
        self.admin_handler = AdminCommandHandler(self.db, logger)

    async def create_daily_sessions(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Create daily sessions"""
        try:
            chat_id = context.job.data['chat_id']
            logger.info(f"Creating daily sessions for chat {chat_id}")
            
            # Simulate create_session command from system
            update = Update(0)  # Create dummy Update
            update.effective_chat = type('obj', (object,), {'id': chat_id})
            await self.admin_handler.create_session(update, context)
            
            logger.info("Daily sessions created successfully")
        except Exception as e:
            logger.error(f"Error creating daily sessions: {e}", exc_info=True)

    def run(self):
            """Run the bot"""
            try:
                # Create application
                application = Application.builder().token(BotConfig.TOKEN).build()

                # Add error handler
                application.add_error_handler(error_handler)

                # Register handlers
                application.add_handler(CommandHandler("help", self.user_handler.help_command))
                application.add_handler(CommandHandler("sessions", self.user_handler.show_sessions))
                application.add_handler(CommandHandler("create_session", self.admin_handler.create_session))
                application.add_handler(CommandHandler("toggle_bot", self.admin_handler.toggle_bot))
                application.add_handler(CommandHandler("stats", self.admin_handler.show_stats))
                application.add_handler(CommandHandler("start", self.user_handler.start))
                
                # Button handlers
                application.add_handler(CallbackQueryHandler(self.user_handler.button_handler))
                
                # Message handlers
                application.add_handler(MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    self.user_handler.handle_message
                ))

                # Setup daily posts schedule
                job_queue = application.job_queue
                job_queue.run_daily(
                    self.create_daily_sessions,
                    time=BotConfig.AUTOPOST_TIME,
                    days=(0, 1, 2, 3, 4, 5, 6),  # All days of week
                    data={'chat_id': os.getenv('TELEGRAM_CHAT_ID')}
                )

                logger.info("Bot started")
                application.run_polling()
                
            except Exception as e:
                logger.error(f"Error starting bot: {e}")
                raise
if __name__ == '__main__':
    bot = VolleyballBot()
    bot.run()