import os
from google import genai
from dotenv import load_dotenv

# Ensure environment is loaded right here
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

client = None

def get_chat_response(message):
    global client
    
    try:
        if client is None:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return "Error: GEMINI_API_KEY is missing in your .env file."
            
            client = genai.Client(api_key=api_key)
            
        system_instruction = "You are a helpful AI career assistant. You help with job search, resume tips, interview preparation, and career guidance. Keep answers clear and concise.\n\n"
        prompt = system_instruction + "User Message: " + message
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Verify if the response successfully completed
        if response.text:
            return response.text
        return "Sorry, I couldn't generate a proper response."
    except Exception as e:
        print("CHATBOT ERROR:", e)
        return "Sorry, something went wrong."
