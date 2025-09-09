from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from dotenv import load_dotenv
from Jarvis_google_search import google_search, get_current_datetime
from jarvis_get_whether import get_weather
from Jarvis_window_CTRL import open_app, close_app, folder_file, shutdown_pc, reboot_pc, sleep_pc
from Jarvis_file_opner import Play_file
from keyboard_mouse_CTRL import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, 
    type_text_tool, press_key_tool, swipe_gesture_tool, 
    press_hotkey_tool, control_volume_tool)
# New imports for email and web control
from Jarvis_email_sender import send_email
from Jarvis_web_controller import open_youtube_in_chrome, open_website
from langchain import hub
import asyncio
from livekit.agents import function_tool
import logging # Import logging

load_dotenv()

# Get the logger
logger = logging.getLogger(__name__)

@function_tool(
    name="thinking_capability",
    description=(
        "Use this tool whenever the user asks to generate or write something new. "
        "If the user does not specify where to write, open Notepad automatically using open_app and start writing. "
        "This tool can also handle tasks like Google search, checking the weather, "
        "opening/closing apps, accessing files, controlling mouse/keyboard, "
        "and system utilities."
))
async def thinking_capability(query: str) -> str:
    """
    LangChain-powered reasoning and action tool.
    Takes a natural language query and executes the appropriate workflow.
    """
    
    # --- ADDED LOGGING ---
    logger.info(f"[Jarvis Reasoning] Received query: {query}")
    
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    
    prompt = hub.pull("hwchase17/react")
    
    tools = [
        google_search,
        get_current_datetime,
        get_weather,
        open_app,
        close_app,
        folder_file,
        Play_file,
        move_cursor_tool,
        mouse_click_tool,
        scroll_cursor_tool,
        type_text_tool,
        press_key_tool,
        press_hotkey_tool,
        control_volume_tool,
        swipe_gesture_tool,
        shutdown_pc,
        reboot_pc,
        sleep_pc,
        send_email,
        open_youtube_in_chrome,
        open_website
    ]

    agent = create_react_agent(
        llm=model,
        tools=tools,
        prompt=prompt
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )

    try:
        result = await executor.ainvoke({"input": query})
        
        final_output = result.get("output", "I encountered an error and could not find an answer.")
        
        # --- ADDED LOGGING ---
        logger.info(f"[Jarvis Reasoning] Raw result from agent: {result}")
        logger.info(f"[Jarvis Reasoning] Final output being sent to voice: {final_output}")
        
        return final_output
    except Exception as e:
        logger.error(f"[Jarvis Reasoning] Agent execution failed: {e}")
        return f"Agent execution failed: {str(e)}"