from keep_alive import keep_alive
#!/usr/bin/env python3
"""
VFS Global Visa Appointment Monitor
Main entry point for the application
"""

import os
import sys
import time
import logging
from datetime import datetime
import pytz
from vfs_monitor import VFSMonitor
from vfs_checker import EnhancedVFSChecker
from telegram_notifier import TelegramNotifier
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('vfs_monitor.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def main():
    keep_alive()
    """Main monitoring loop"""
    logger.info("Starting VFS Global Visa Appointment Monitor")
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize components
        telegram_notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
        vfs_monitor = VFSMonitor(config.vfs_email, config.vfs_password)
        enhanced_checker = EnhancedVFSChecker(config.vfs_email, config.vfs_password)
        
        # Send startup notification (without test)
        morocco_tz = pytz.timezone('Africa/Casablanca')
        start_time = datetime.now(morocco_tz)
        telegram_notifier.send_message(f"🤖 VFS Appointment Monitor Started\nMonitoring Italy visa appointments in Morocco with enhanced detection methods...\n\n⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        last_check_time = None
        consecutive_errors = 0
        max_consecutive_errors = 5
        use_enhanced_method = False
        
        while True:
            try:
                current_time = datetime.now(config.timezone)
                logger.info(f"Checking for appointments at {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                
                # Check for appointments using primary or enhanced method
                appointments = []
                
                if not use_enhanced_method:
                    try:
                        appointments = vfs_monitor.check_appointments()
                    except Exception as e:
                        logger.warning(f"Primary method failed: {str(e)}")
                        logger.info("Switching to enhanced monitoring method")
                        use_enhanced_method = True
                
                if use_enhanced_method or not appointments:
                    try:
                        enhanced_appointments = enhanced_checker.check_availability()
                        if enhanced_appointments:
                            appointments.extend(enhanced_appointments)
                            logger.info("Enhanced method detected potential appointments")
                    except Exception as e:
                        logger.error(f"Enhanced method also failed: {str(e)}")
                
                if appointments:
                    logger.info(f"Found {len(appointments)} available appointments")
                    
                    # Send notification for each appointment
                    for appointment in appointments:
                        message = format_appointment_message(appointment)
                        telegram_notifier.send_message(message)
                        logger.info(f"Notification sent for appointment: {appointment}")
                else:
                    logger.info("No appointments available")
                
                last_check_time = current_time
                consecutive_errors = 0  # Reset error counter on success
                
            except Exception as e:
                consecutive_errors += 1
                error_msg = f"Error checking appointments (attempt {consecutive_errors}/{max_consecutive_errors}): {str(e)}"
                logger.error(error_msg)
                
                # Send error notification after multiple failures
                if consecutive_errors >= 3:
                    telegram_notifier.send_message(f"⚠️ Monitor Warning\n{error_msg}")
                
                # Stop if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    error_msg = f"Too many consecutive errors ({max_consecutive_errors}). Stopping monitor."
                    logger.critical(error_msg)
                    telegram_notifier.send_message(f"🚨 Monitor Stopped\n{error_msg}")
                    break
            
            # Wait for next check
            logger.info(f"Waiting {config.check_interval} seconds until next check...")
            time.sleep(config.check_interval)
            
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        telegram_notifier.send_message("🛑 VFS Monitor stopped by user")
    except Exception as e:
        error_msg = f"Critical error in main loop: {str(e)}"
        logger.critical(error_msg)
        try:
            telegram_notifier.send_message(f"🚨 Critical Error\n{error_msg}")
        except:
            pass  # Don't let notification errors crash the error handler
        raise

def format_appointment_message(appointment):
    """Format appointment data into a readable Telegram message"""
    message = "🎯 **VISA APPOINTMENT AVAILABLE!**\n\n"
    message += f"📍 **Location:** {appointment.get('location', 'Italy Visa Center Morocco')}\n"
    message += f"📅 **Date:** {appointment.get('date', 'Not specified')}\n"
    message += f"⏰ **Time:** {appointment.get('time', 'Not specified')}\n"
    
    if appointment.get('link'):
        message += f"🔗 **Book Now:** {appointment['link']}\n"
    
    # Add confidence level if available
    if appointment.get('confidence'):
        confidence_emoji = "🔴" if appointment['confidence'] == 'low' else "🟡" if appointment['confidence'] == 'medium' else "🟢"
        message += f"{confidence_emoji} **Confidence:** {appointment['confidence'].title()}\n"
    
    # Add detection method if available
    if appointment.get('source'):
        message += f"📊 **Source:** {appointment['source']}\n"
    
    message += f"\n⚡ **Action Required:** Log in to VFS Global immediately to book this slot!\n"
    message += f"🌐 **Website:** https://visa.vfsglobal.com/mar/fr/ita/dashboard\n"
    # Get Morocco timezone
    morocco_tz = pytz.timezone('Africa/Casablanca')
    current_time = datetime.now(morocco_tz)
    message += f"⏱️ **Found at:** {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    
    # Add note if available
    if appointment.get('note'):
        message += f"\n\n💡 **Note:** {appointment['note']}"
    
    return message

if __name__ == "__main__":
    main()
