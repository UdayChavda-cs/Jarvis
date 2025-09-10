import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, RoomInputOptions, ChatContext, ChatMessage, ChatRole
from livekit.plugins import google, noise_cancellation
from datetime import datetime

from Jarvis_prompts import instructions_prompt, BASE_REPLY_PROMPT 
from memory_store import ConversationMemory
from jarvis_reasoning import thinking_capability

load_dotenv()

USER_ID = "uday_chavda_main_user" 

def get_dynamic_greeting_prompt():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "फिर current समय के आधार पर user को greet कीजिए और बोलिए: 'Good morning!'"
    elif 12 <= hour < 18:
        greeting = "फिर current समय के आधार पर user को greet कीजिए और बोलिए: 'Good afternoon!'"
    else:
        greeting = "फिर current समय के आधार पर user को greet कीजिए और बोलिए: 'Good evening!'"
    
    return BASE_REPLY_PROMPT.format(greeting_instruction=greeting)

class Assistant(Agent):
    def __init__(self, memory: ConversationMemory):
        recent_history_dicts = memory.get_recent_context(max_messages=20)
        chat_messages = []
        for msg in recent_history_dicts:
            try:
                role_str = str(msg.get("role", "user")).upper()
                role = ChatRole.USER if "USER" in role_str else ChatRole.ASSISTANT
                
                content = msg.get("text", "")
                if isinstance(content, list):
                    content = " ".join(content)
                
                chat_messages.append(ChatMessage(content=content, role=role))
            except Exception as e:
                print(f"Skipping malformed message: {msg} - Error: {e}")
                continue

        initial_ctx = ChatContext(chat_messages)

        super().__init__(
            instructions=instructions_prompt,
            llm=google.beta.realtime.RealtimeModel(voice="Charon"),
            tools=[thinking_capability],
            chat_ctx=initial_ctx
        )
        self.memory = memory


async def entrypoint(ctx: JobContext):
    memory = ConversationMemory(user_id=USER_ID)
    
    session = AgentSession(
        preemptive_generation=True
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(memory=memory),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    
    dynamic_greeting = get_dynamic_greeting_prompt()
    await session.generate_reply(
        instructions=dynamic_greeting
    )
    
    final_history = session.history.items
    if final_history:
        messages_to_save = []
        for msg in final_history:
            content_to_save = msg.content
            if isinstance(content_to_save, list):
                content_to_save = " ".join(content_to_save)
            
            messages_to_save.append({
                "role": str(msg.role), 
                "text": content_to_save,
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