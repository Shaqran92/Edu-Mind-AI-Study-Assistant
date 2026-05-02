def speak_text(text: str):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)