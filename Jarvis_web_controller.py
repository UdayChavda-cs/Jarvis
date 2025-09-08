import asyncio
import logging
from langchain.tools import tool

# Import only the controller, not other tools
from keyboard_mouse_CTRL import controller

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Chrome path directly, as found in your Jarvis_window_CTRL.py file
# Make sure this path is correct for your system
CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"

@tool
async def open_youtube_in_chrome(search_query: str = "") -> str:
    """
    Opens Google Chrome, then navigates to YouTube and optionally performs a search using keyboard simulation.

    Use this tool for ANY request involving opening or searching YouTube.
    Example prompts:
    - "Open YouTube"
    - "YouTube kholo"
    - "Search for cat videos on YouTube"
    """
    try:
        # Step 1: Open the Chrome application using its direct path
        logger.info("🌐 Opening Google Chrome...")
        # Replicate the core logic from the open_app tool to avoid errors
        await asyncio.create_subprocess_shell(f'start "" "{CHROME_PATH}"', shell=True)

        # Wait for Chrome to fully open and be the active window
        await asyncio.sleep(4)

        # Step 2: Manually activate the controller for typing/pressing keys
        controller.activate("my_secret_token")
        
        # Step 3: Type the URL or a search query
        if search_query:
            # If there's a search query, type the full search URL
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            logger.info(f"Typing search URL: {search_url}")
            await controller.type_text(search_url)
        else:
            # Otherwise, just type the website address
            logger.info("Typing YouTube URL: youtube.com")
            await controller.type_text("youtube.com")

        await asyncio.sleep(0.5) # A brief pause after typing

        # Step 4: Press the Enter key
        logger.info("Pressing Enter key.")
        await controller.press_key("enter")
        
        # Step 5: Deactivate the controller after the actions are done
        await asyncio.sleep(2) # Wait a moment before deactivating
        controller.deactivate()

        return f"✅ Opened YouTube in Chrome. {'Searching for ' + search_query if search_query else ''}"
    
    except FileNotFoundError:
        logger.error(f"❌ Chrome not found at path: {CHROME_PATH}")
        return f"❌ Google Chrome could not be found. Please check the path in the script."
    except Exception as e:
        # Ensure the controller is deactivated in case of an error
        if controller.is_active():
            controller.deactivate()
        logger.error(f"❌ Failed during the YouTube opening process: {e}")
        return f"❌ An error occurred while trying to open YouTube in Chrome: {e}"