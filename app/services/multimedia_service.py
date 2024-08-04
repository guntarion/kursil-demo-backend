import requests
import os
from dotenv import load_dotenv
from bson import ObjectId
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("ELEVENLABS_API_KEY")


def topic_text_to_speech(main_topic_id: str, text: str, voice_id: str):
    # ElevenLabs API endpoint
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    speaking_rate = 0.9  # Adjust this value to make it slower or faster

    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "use_speaker_boost": True,
            "speaking_rate": speaking_rate
        }
    }

    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    logger.debug(f"Sending request to ElevenLabs API:")
    logger.debug(f"URL: {url}")
    logger.debug(f"Headers: {headers}")
    logger.debug(f"Payload: {payload}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content: {response.text}")

        response.raise_for_status()  # Raise an exception for bad status codes

        # Check if the request was successful
        if response.status_code == 200:
            # Create the resources directory if it doesn't exist
            os.makedirs("./resources", exist_ok=True)

            # Generate the filename
            output_filename = f"./resources/{main_topic_id}_pitch.mp3"

            # Save the audio content to a file
            with open(output_filename, "wb") as audio_file:
                audio_file.write(response.content)
            logger.info(f"Audio file saved as '{output_filename}'")
            return {"message": f"Audio file saved as '{output_filename}'", "filename": output_filename}
        else:
            logger.error(
                f"Error response from ElevenLabs API: {response.status_code} - {response.text}")
            return {"error": f"Error: {response.status_code} - {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception occurred: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}
