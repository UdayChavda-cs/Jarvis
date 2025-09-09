import os
import subprocess
import logging
import sys
import asyncio
from fuzzywuzzy import process

# Import ctypes for UAC elevation on Windows
try:
    import ctypes
except ImportError:
    ctypes = None

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

from langchain.tools import tool

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Function for Admin Privileges (inside Jarvis_window_CTRL.py) ---
def run_command_as_admin(command):
    """
    Executes a command with administrator privileges, prompting UAC if necessary.
    """
    if sys.platform != 'win32' or not ctypes:
        return subprocess.run(command, shell=True)

    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            logger.info(f"Requesting UAC elevation for command: '{command}'")
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {command}", None, 1)
            
            if ret > 32:
                return "✅ UAC prompt shown. The command is being executed with admin rights."
            else:
                # Log the specific error code for debugging
                error_message = f"Failed to show UAC prompt. Windows error code: {ret}"
                logger.error(error_message)
                return f"❌ {error_message}"
        else:
            logger.info(f"Already admin. Executing command directly: '{command}'")
            # Use capture_output to log any errors from the command
            result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True)
            if result.returncode != 0:
                error_output = result.stderr or result.stdout
                logger.error(f"Command failed with return code {result.returncode}: {error_output.strip()}")
                return f"❌ Command failed: {error_output.strip()}"
            return f"✅ Command executed with existing admin rights."
            
    except Exception as e:
        error_message = f"An exception occurred while trying to run command as admin: {e}"
        logger.error(error_message)
        return f"❌ {error_message}"
# App command map
APP_MAPPINGS = {
    "notepad": "notepad",
    "calculator": "calc",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
    "command prompt": "cmd",
    "control panel": "control",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "vs code": "C:\\Users\\Uday\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
    "postman": "C:\\Users\\Uday\\AppData\\Local\\Postman\\Postman.exe",
    "Jio shpare browser": "C:\\Users\\Uday\\AppData\\Local\\JIO\\JioSphere\\Application\\JioSphere.exe"
}

# (The rest of the file remains the same, but the power functions are updated)
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow")
        return False

    await asyncio.sleep(1.5)  # Give time for window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
            for f in files:
                item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"✅ Indexed {len(item_index)} items.")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया। {e}")

async def play_file(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया।: {e}")

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder create हो गया।: {path}"
    except Exception as e:
        return f"❌ फ़ाइल create करने में error आया।: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ नाम बदलकर {new_path} कर दिया गया।"
    except Exception as e:
        return f"❌ नाम बदलना fail हो गया: {e}"

async def delete_item(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ Deleted: {path}"
    except Exception as e:
        return f"❌ Delete नहीं हुआ।: {e}"

# App control
@tool
async def open_app(app_title: str) -> str:
    """
    open_app a desktop app like Notepad, Chrome, VLC, etc.

    Use this tool when the user asks to launch an application on their computer.
    Example prompts:
    - "Notepad खोलो"
    - "Chrome open करो"
    - "VLC media player चलाओ"
    - "Calculator launch करो"
    """
    app_title = app_title.lower().strip()
    app_command = APP_MAPPINGS.get(app_title, app_title)
    try:
        subprocess.Popen(f'start "" "{app_command}"', shell=True)
        focused = await focus_window(app_title)
        if focused:
            return f"🚀 App launch हुआ और focus में है: {app_title}."
        else:
            return f"🚀 {app_title} Launch किया गया, लेकिन window पर focus नहीं हो पाया।"
    except Exception as e:
        return f"❌ {app_title} Launch नहीं हो पाया।: {e}"

@tool
async def close_app(window_title: str) -> str:
    """
    Closes the applications window by its title.

    Use this tool when the user wants to close any app or window on their desktop.
    Example prompts:
    - "Notepad बंद करो"
    - "Close VLC"
    - "Chrome की window बंद कर दो"
    - "Calculator को बंद करो"
    """
    if not win32gui:
        return "❌ win32gui"
    def enumHandler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    win32gui.EnumWindows(enumHandler, None)
    return f"✅ Sent close command to window: {window_title}"

# Jarvis command logic
@tool
async def folder_file(command: str) -> str:
    """
    Handles folder and file actions like open, create, rename, or delete based on user command.

    Use this tool when the user wants to manage folders or files using natural language.
    Example prompts:
    - "Projects folder बनाओ"
    - "OldName को NewName में rename करो"
    - "xyz.mp4 delete कर दो"
    - "Music folder खोलो"
    - "Resume.pdf चलाओ"
    """
    folders_to_index = ["D:/"]
    index = await index_items(folders_to_index)
    command_lower = command.lower()
    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)
    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ rename command valid नहीं है।"
    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ Delete करने के लिए item नहीं मिला।"
    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"✅ Folder opened: {item['name']}"
        return "❌ Folder नहीं मिला।."
    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"✅ File opened: {item['name']}"
    return "⚠ कुछ भी match नहीं हुआ।"

# --- UPDATED POWER FUNCTIONS ---

@tool
async def shutdown_pc() -> str:
    """
    Shuts down the computer, requesting administrator permission if needed.
    """
    return run_command_as_admin("shutdown /s /t 1")

@tool
async def reboot_pc() -> str:
    """
    Reboots the computer, requesting administrator permission if needed.
    """
    return run_command_as_admin("shutdown /r /t 1")

@tool
async def sleep_pc() -> str:
    """
    Puts the computer to sleep, requesting administrator permission if needed.
    """
    return run_command_as_admin("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")