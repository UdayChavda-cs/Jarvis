import pvporcupine
import pyaudio
import struct
import subprocess
import sys

# TODO: Replace with your Picovoice Access Key
ACCESS_KEY = "2ADtkfaJVgugHkfnrhtNNsbyqHMSugGB5d4uNCZg5z6ARLB7P3+AOA==" 

# This uses the built-in "jarvis" keyword model
KEYWORD_PATHS = [pvporcupine.KEYWORD_PATHS["jarvis"]]

porcupine = None
pa = None
audio_stream = None

print("Initializing Wake Word Listener...")
try:
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=KEYWORD_PATHS
    )

    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("="*50)
    print(f"Listening for 'Jarvis'... (Press Ctrl+C to exit)")
    print("="*50)

    while True:
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        result = porcupine.process(pcm)
        if result >= 0:
            print("Wake word 'Jarvis' detected! Starting main agent...")
            
            # This command will start your main Jarvis application.
            # Make sure 'agent.py' is the correct entry point.
            # On Windows, you might need to use "python" instead of "python3"
            try:
                # --- THIS IS THE UPDATED LINE ---
                # We now run "python agent.py console"
                subprocess.Popen([sys.executable, "agent.py", "console"])
                print("Main agent process started.")
            except FileNotFoundError:
                print("Error: 'agent.py' not found. Make sure you are in the correct directory.")
            except Exception as e:
                print(f"Failed to start agent.py: {e}")


except pvporcupine.PorcupineActivationError as e:
    print(f"Porcupine activation error: {e}")
    print("Please make sure your Access Key is valid and not expired.")
except pvporcupine.PorcupineError as e:
    print(f"An error occurred with Porcupine: {e}")
except KeyboardInterrupt:
    print("Stopping listener.")
finally:
    if audio_stream is not None:
        audio_stream.close()
    if pa is not None:
        pa.terminate()
    if porcupine is not None:
        porcupine.delete()
    print("Cleanup complete. Exiting.")