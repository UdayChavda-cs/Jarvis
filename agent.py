import asyncio
from dotenv import load_dotenv
from livekit import agents
# Import ChatContext, ChatMessage, and ChatRole for history management
from livekit.agents import Agent, AgentSession, JobContext, RoomInputOptions, ChatContext, ChatMessage, ChatRole
from livekit.plugins import google, noise_cancellation

from Jarvis_prompts import instructions_prompt, Reply_prompts
from memory_store import ConversationMemory
from jarvis_reasoning import thinking_capability

load_dotenv()

# A unique identifier for the user. In a real application, this would be dynamic.
USER_ID = "uday_chavda_main_user" 

class Assistant(Agent):
    def __init__(self, memory: ConversationMemory):
        # 1. Load the recent message history from our persistent memory
        recent_history_dicts = memory.get_recent_context(max_messages=20)
        
        # 2. Convert the dictionaries from the JSON file back into ChatMessage objects
        chat_messages = []
        for msg in recent_history_dicts:
            try:
                # The role is saved as a string, so we convert it back to the ChatRole enum
                role_str = str(msg.get("role", "user")).upper()
                if "USER" in role_str:
                    role = ChatRole.USER
                else:
                    role = ChatRole.ASSISTANT
                
                chat_messages.append(ChatMessage(text=msg.get("text", ""), role=role))
            except Exception as e:
                # Skip any malformed messages in the history file
                print(f"Skipping malformed message: {msg} - Error: {e}")
                continue

        # 3. THE FIX: Create a new ChatContext by passing the list of messages as a POSITIONAL argument
        initial_ctx = ChatContext(chat_messages)

        # 4. Pass the pre-populated context to the parent Agent class during initialization
        super().__init__(
            instructions=instructions_prompt,
            llm=google.beta.realtime.RealtimeModel(voice="Charon"),
            tools=[thinking_capability],
            chat_ctx=initial_ctx  # Pass the populated context here
        )
        self.memory = memory


async def entrypoint(ctx: JobContext):
    """
    This is the main entry point for the agent.
    It's called when a new job is created.
    """
    # Initialize conversation memory for the user
    memory = ConversationMemory(user_id=USER_ID)
    
    session = AgentSession(
        preemptive_generation=True
    )

    # Start the agent session with the memory-aware assistant
    await session.start(
        room=ctx.room,
        agent=Assistant(memory=memory),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    
    # Generate the initial greeting
    await session.generate_reply(
        instructions=Reply_prompts
    )
    
    # After the session ends, save the full conversation
    final_history = session.history.items
    if final_history:
        messages_to_save = []
        for msg in final_history:
            messages_to_save.append({
                "role": str(msg.role), # Save the role as a string for JSON compatibility
                "text": msg.text,
                "id": msg.id,
            })
            
        conversation_data = {
            "messages": messages_to_save
        }
        
        print("Conversation ended. Saving history...")
        success = memory.save_conversation(conversation_data)
        if success:
            print(f"Successfully saved {len(messages_to_save)} messages.")
        else:
            print("Failed to save conversation history.")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))