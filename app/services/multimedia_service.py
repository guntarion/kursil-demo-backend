# app/services/multimedia_service.py
import requests
import os
from dotenv import load_dotenv
from bson import ObjectId
import logging
from datetime import datetime

from app.utils.digitalocean_spaces import upload_file_to_spaces
from app.db.operations import update_main_topic_document

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("ELEVENLABS_API_KEY")


# app/services/multimedia_service.py
async def topic_text_to_speech(main_topic_id: str, text: str, voice_id: str):
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
        logger.debug(f"Response content length: {len(response.content)} bytes")

        response.raise_for_status()  # Raise an exception for bad status codes

        # Check if the request was successful
        if response.status_code == 200:
            # Create the resources directory if it doesn't exist
            os.makedirs("./resources", exist_ok=True)

            # Generate the filename
            date_str = datetime.now().strftime("%y_%m_%d_%H_%M")
            output_filename = f"./resources/{date_str}_{main_topic_id}_pitch.mp3"

            # Save the audio content to a file
            with open(output_filename, "wb") as audio_file:
                audio_file.write(response.content)
            logger.info(f"Audio file saved as '{output_filename}'")

            # Upload the audio to DigitalOcean Spaces
            file_url = upload_file_to_spaces(output_filename)

            if file_url:
                # Update the main_topic_collection with the new audio URL
                updated = await update_main_topic_document(main_topic_id, {"link_audio_pitch": file_url})
                if not updated:
                    raise ValueError("Failed to update main topic with new audio URL")

                # Clean up the local file
                os.remove(output_filename)
                logger.info(f"Local file {output_filename} deleted after successful upload")

                return {"message": f"Audio file uploaded successfully", "file_url": file_url}
            else:
                logger.error("Failed to upload file to DigitalOcean Spaces")
                return {"error": "Failed to upload file to DigitalOcean Spaces"}
        else:
            logger.error(
                f"Error response from ElevenLabs API: {response.status_code} - {response.text}")
            return {"error": f"Error: {response.status_code} - {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception occurred: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}