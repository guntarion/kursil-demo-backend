# fastapi app/services/openai_service.py
import asyncio
from bson import ObjectId
import os
import re
from fastapi import HTTPException
from openai import OpenAI
from typing import List, Dict
from dotenv import load_dotenv
import tiktoken
from app.services.cost_calculator import calculate_cost
from app.db.database import main_topic_collection, list_topics_collection, cost_ai_collection
from app.db.operations import get_topic_by_name, add_elaborated_point, add_elaborated_point, get_topic_by_name, update_main_topic_document
from app.utils.digitalocean_spaces import upload_file_to_spaces
from datetime import datetime
import base64
from deep_translator import GoogleTranslator
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def read_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def count_tokens(text):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    return len(tokens)

def parse_generated_content(content):
    sections = content.split('\n\n')
    topics = []
    topic_pattern = re.compile(r'\d+\.\s+\*\*Topic Title:\*\* (.*?)\n', re.DOTALL)
    objective_pattern = re.compile(r'- \*\*Objective:\*\* (.*?)(?:\n|$)', re.DOTALL)
    key_concepts_pattern = re.compile(r'- \*\*Key Concepts:\*\* (.*?)(?:\n|$)', re.DOTALL)
    skills_pattern = re.compile(r'- \*\*Skills to be Mastered:\*\* (.*?)(?:\n|$)', re.DOTALL)
    discussion_pattern = re.compile(r'- \*\*Point of Discussion:\*\*\n(.*?)(?=\n\s*\n|\Z)', re.DOTALL)

    parsed_topics = []

    for section in sections:
        topic_match = topic_pattern.search(section)
        if topic_match:
            topic = {
                "topic_name": topic_match.group(1).strip(),
                "objective": objective_pattern.search(section).group(1).strip() if objective_pattern.search(section) else "",
                "key_concepts": key_concepts_pattern.search(section).group(1).strip() if key_concepts_pattern.search(section) else "",
                "skills_to_be_mastered": skills_pattern.search(section).group(1).strip() if skills_pattern.search(section) else "",
                "point_of_discussion": []
            }
            
            discussion_match = discussion_pattern.search(section)
            if discussion_match:
                discussion_points = discussion_match.group(1).strip().split('\n')
                topic["point_of_discussion"] = [point.strip('- ').strip() for point in discussion_points]
            
            parsed_topics.append(topic)

    return parsed_topics

def generate_summary(parsed_topics):
    prompt = "Generate a concise and coherent summary of the learning objectives based on the following information about several learning topics. This summary will be included in a curriculum document to offer a general overview of what participants will achieve through the training program. The summary should integrate the objectives from each topic to highlight the program's overall educational goals, ensuring clarity and alignment with the intended learning outcomes. Provide only the summary and nothing else.\n\n"

    for topic in parsed_topics:
        prompt += f"Topic: {topic['topic_name']}\nObjective: {topic['objective']}\n\n"

    messages = [
        {"role": "system", "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    summary = completion.choices[0].message.content.strip()
    return summary

def create_listof_topic(topic):
    # Read the prompt template
    prompt_template = read_prompt("./app/prompts/prompt_listof_topic.txt")

    # Replace the placeholder with the actual topic
    prompt = prompt_template.replace("{{topic}}", topic)

    messages = [
        {"role": "system",
            "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    list_of_topics = completion.choices[0].message.content.strip()

    # Calculate cost based on the output
    prompt_input_token_count = count_tokens(prompt)
    prompt_output_token_count = count_tokens(list_of_topics)
    total_cost_idr = calculate_cost(
        prompt_input_token_count, prompt_output_token_count)

    # Parse the generated content
    parsed_topics = parse_generated_content(list_of_topics)

    parsed_topics = parse_generated_content(list_of_topics)

    # Generate summary
    summary = generate_summary(parsed_topics)

    # Calculate additional cost for summary generation
    summary_prompt_token_count = count_tokens(prompt)
    summary_output_token_count = count_tokens(summary)
    summary_cost = calculate_cost(summary_prompt_token_count, summary_output_token_count)

    total_cost_idr += summary_cost

    # Save to MongoDB
    main_topic_data = {
        "main_topic": topic,
        "cost": total_cost_idr,
        "list_of_topics": [t["topic_name"] for t in parsed_topics],
        "main_topic_objective": summary,
        "latest_kursil_document": str,  # Path to the latest generated Kursil document
        "latest_handout_document": str,  # Path to the latest generated Handout document
        "latest_powerpoint_document": str,  # Path to the latest generated Powerpoint document
        "link_image_icon": str, 
        "link_audio_pitch": str 
    }
    result = main_topic_collection.insert_one(main_topic_data)
    main_topic_id = str(result.inserted_id)

    for topic in parsed_topics:
        topic["main_topic_id"] = main_topic_id
        list_topics_collection.insert_one(topic)

    return {
        "main_topic_id": main_topic_id,
        "cost": total_cost_idr,
        "generated_content": parsed_topics,
        "main_topic_objective": summary
    }

def translate_points(points: List[str]) -> List[str]:
    prompt = "Translate the following points of discussion to Bahasa Indonesia:\n\n"
    for i, point in enumerate(points, 1):
        prompt += f"{i}. {point}\n"

    messages = [
        {"role": "system", "content": "You are a professional translator specializing in English to Bahasa Indonesia translations."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    translated_text = completion.choices[0].message.content.strip()
    translated_points = translated_text.split('\n')
    return [point.split('. ', 1)[1] if '. ' in point else point for point in translated_points]



async def elaborate_discussionpoint(topic: str, objective: str, points_of_discussion: List[str]) -> List[Dict[str, str]]:
    prompt_template = read_prompt("./app/prompts/prompt_detaillistof_discussionpoint.txt")

    points_str = "\n".join([f"  - {point}" for point in points_of_discussion])
    prompt = prompt_template.format(topic=topic, objective=objective, pointsofdiscussion=points_str)

    messages = [
        {"role": "system", "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
        {"role": "user", "content": prompt}
    ]

    # Calculate input tokens
    input_token_count = count_tokens(prompt)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    elaborated_content = completion.choices[0].message.content.strip()

    # Calculate output tokens
    output_token_count = count_tokens(elaborated_content)

    # Calculate cost
    total_cost_idr = calculate_cost(input_token_count, output_token_count)

    # Parse the elaborated content into a structured format
    elaborated_points = []
    current_subtopic = None
    current_elaboration = []

    for line in elaborated_content.split('\n'):
        line = line.strip()
        logger.debug(f"Processing line: {line}")

        if '**Subtopic:**' in line:
            if current_subtopic:
                elaborated_points.append({
                    "subtopic": current_subtopic,
                    "elaboration": '\n'.join(current_elaboration)
                })
            current_subtopic = line.split('**Subtopic:**')[1].strip()
            current_elaboration = []
            logger.debug(f"Found new subtopic: {current_subtopic}")
        elif '**Discussion Points Elaboration:**' not in line and line:  # Non-empty line and not the omitted line
            current_elaboration.append(line)
            logger.debug(f"Added line to current elaboration: {line}")

    # Add the last subtopic
    if current_subtopic:
        elaborated_points.append({
            "subtopic": current_subtopic,
            "elaboration": '\n'.join(current_elaboration)
        })

    # Store elaborated points in the database and get the topic_id
    topic_doc = await get_topic_by_name(topic)
    topic_id = None
    if topic_doc:
        topic_id = topic_doc['_id']
        for point in elaborated_points:
            await add_elaborated_point(point['subtopic'], point['elaboration'], topic_id)

    # Store cost information in cost_ai_collection
    cost_data = {
        "datetime": datetime.utcnow(),
        "topic_id": str(topic_id),
        "content": topic,
        "process_name": "elaboration",
        "cost": round(total_cost_idr)  
    }
    cost_ai_collection.insert_one(cost_data)

    return elaborated_points


# 🔰 Individual functions to generate prompting
async def generate_prompting(elaboration: str, point_of_discussion: str, topic_id: str) -> str:
    prompt_template = read_prompt("./app/prompts/prompt_create_prompttowrite.txt")
    
    prompt = prompt_template.replace("{point_of_discussion}", point_of_discussion)
    prompt = prompt.replace("{elaboration}", elaboration)

    messages = [
        {"role": "system", "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
        {"role": "user", "content": prompt}
    ]

    # Calculate input tokens
    input_token_count = count_tokens(prompt)

    # Use asyncio.to_thread to run the synchronous OpenAI call in a separate thread
    completion = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o-mini",
        messages=messages
    )

    prompting_content = completion.choices[0].message.content.strip()

    # Calculate output tokens
    output_token_count = count_tokens(prompting_content)

    # Calculate cost
    total_cost_idr = calculate_cost(input_token_count, output_token_count)

    # Store cost information in cost_ai_collection
    cost_data = {
        "datetime": datetime.utcnow(),
        "topic_id": str(topic_id),
        "content": point_of_discussion,
        "process_name": "prompting",
        "cost": round(total_cost_idr)
    }
    await asyncio.to_thread(cost_ai_collection.insert_one, cost_data)

    return prompting_content

async def generate_handout(point_of_discussion: str, prompting: str, topic_id: str) -> str:
    if not prompting:
        logger.warning(f"Prompting is empty for point of discussion: {point_of_discussion}")
        return ""
    
    myprompt = f"The topic is {point_of_discussion} and here's the detail instruction: {prompting}"

    messages = [
        {
            "role": "system",
            "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields. Create a detailed and comprehensive section for a book chapter that addresses the provided discussion points. The content should be tailored for PLN Persero employees who have diverse educational backgrounds, ensuring that the explanations are technically informative yet understandable for non-technical staff. The aim of this book chapter is to provide PLN Persero employees with a well-rounded understanding of the provided discussion points."
        },
        {
            "role": "user",
            "content": myprompt
        }
    ]

    input_token_count = count_tokens(myprompt)

    completion = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-4o-mini",
        messages=messages
    )

    handout_content = completion.choices[0].message.content.strip()

    output_token_count = count_tokens(handout_content)
    total_cost_idr = calculate_cost(input_token_count, output_token_count)

    cost_data = {
        "datetime": datetime.utcnow(),
        "topic_id": str(topic_id),
        "content": point_of_discussion,
        "process_name": "handout",
        "cost": round(total_cost_idr)
    }
    await asyncio.to_thread(cost_ai_collection.insert_one, cost_data)

    return handout_content

async def generate_misc_points(point_of_discussion: str, handout: str, topic_id: str) -> dict:
    if not handout:
        logger.warning(f"Handout is empty for point of discussion: {point_of_discussion}")
        return ""    
    
    prompt_template = read_prompt("./app/prompts/prompt_misc_points.txt")
    my_prompt = prompt_template + f"Topiknya {point_of_discussion} dan berikut adalah informasinya: {handout}"

    messages = [
        {
            "role": "system",
            "content": "Anda adalah seorang pengembang konten edukasi dan merupakan konsultan untuk Pusdiklat PLN yang mendukung Perusahaan Listrik Negara (PLN) dalam menjalankan bisnis ketenagalistrikan dan bidang-bidang terkait lainnya. Anda harus memberikan jawaban dalam bahasa Indonesia."
        },
        {
            "role": "user",
            "content": my_prompt
        }
    ]

    try:
        input_token_count = count_tokens(my_prompt)

        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=messages
        )

        response = completion.choices[0].message.content.strip()
        logger.debug(f"\n😊 ==!== OpenAI response: {response}")

        output_token_count = count_tokens(response)
        total_cost_idr = calculate_cost(input_token_count, output_token_count)

        cost_data = {
            "datetime": datetime.utcnow(),
            "topic_id": str(topic_id),
            "content": point_of_discussion,
            "process_name": "misc_points",
            "cost": round(total_cost_idr)
        }
        await asyncio.to_thread(cost_ai_collection.insert_one, cost_data)

        # Parse the response (existing code)
        method = re.search(r'\[Usulan Durasi Waktu\]\n\n(.*?)(?=\*\*Durasi Total\*\*|\n###|\Z)', response, re.DOTALL)
        assessment = re.search(r'\[Identifikasi Kriteria Penilaian\]\n\n(.*?)(?=\n###|\Z)', response, re.DOTALL)
        learn_objective = re.search(r'\[Tujuan Pembelajaran\]\n\n(.*?)(?=\n###|\Z)', response, re.DOTALL)

        duration_match = re.search(r'\*\*Durasi Total\*\*:\s*(\d+)\s*menit', response)
        duration = int(duration_match.group(1))

        logger.debug(f"\n\n==!!-- str(topic_id): {str(topic_id)}")
        logger.debug(f"==!!-- point_of_discussion: {point_of_discussion}")
        logger.debug(f"==!!-- method: {method.group(1).strip() if method else ''}")
        logger.debug(f"==!!-- assessment: {assessment.group(1).strip() if assessment else ''}")
        logger.debug(f"==!!-- learn_objective: {learn_objective.group(1).strip() if learn_objective else ''}")
        logger.debug(f"==!!-- duration: {duration}\n\n")


        result = {
            "method": method.group(1).strip() if method else "",
            "assessment": assessment.group(1).strip() if assessment else "",
            "learn_objective": learn_objective.group(1).strip() if learn_objective else "",
            "duration": duration
        }

        return result
    except Exception as e:
        logger.error(f"Error generating misc points: {str(e)}")
        raise

async def generate_quiz(point_of_discussion: str, handout: str, topic_id: str) -> str:
    if not handout:
        logger.warning(f"Handout is empty for point of discussion: {point_of_discussion}")
        return ""        
    
    prompt_template = read_prompt("./app/prompts/prompt_quiz.txt")
    my_prompt = prompt_template + f"The topic is {point_of_discussion} and here's the information: {handout}"

    messages = [
        {
            "role": "system",
            "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields. Provide response in bahasa Indonesia."
        },
        {
            "role": "user",
            "content": my_prompt
        }
    ]

    try:
        input_token_count = count_tokens(my_prompt)

        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=messages
        )

        response = completion.choices[0].message.content.strip()
        logger.debug(f"OpenAI response for quiz: {response}")

        output_token_count = count_tokens(response)
        total_cost_idr = calculate_cost(input_token_count, output_token_count)

        cost_data = {
            "datetime": datetime.utcnow(),
            "topic_id": str(topic_id),
            "content": point_of_discussion,
            "process_name": "quiz",
            "cost": round(total_cost_idr)
        }
        await asyncio.to_thread(cost_ai_collection.insert_one, cost_data)

        # Remove the '#### Kuis Pilihan Ganda' text if present
        cleaned_response = response.replace('#### Kuis Pilihan Ganda', '').strip()
        logger.debug(f"Cleaned quiz content: {cleaned_response}")

        return cleaned_response

    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise

def generate_handout_translation(handout: str) -> str:
    try:
        translator = GoogleTranslator(source='en', target='id')
        # Translate in chunks of 5000 characters to avoid length limits
        chunks = [handout[i:i+3000] for i in range(0, len(handout), 3000)]
        translated_chunks = [translator.translate(chunk) for chunk in chunks]

        # Join the translated chunks back into a single string
        translated_handout = ' '.join(translated_chunks)

        logger.debug(f"Translated handout: {translated_handout}")
        return translated_handout
    except Exception as e:
        logger.error(f"Error translating handout: {str(e)}")
        raise    


async def generate_topic_imageicon(topic: str, main_topic_id: str) -> str:
    prompt = f"Create a color minimalist icon-like image depicting the information of the training topic: {topic}. The image should be simple, professional, and easily recognizable. There should not be any text on the image."

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        logger.debug(f"OpenAI API response: {response}")

        if not response.data:
            raise ValueError("No image data in the response")

        image_url = response.data[0].url

        if not image_url:
            raise ValueError("No image URL in the response")

        # Download the image from the URL
        image_response = requests.get(image_url)
        image_response.raise_for_status()  # Raise an exception for bad status codes

        # Create the resources directory if it doesn't exist
        os.makedirs("./resources", exist_ok=True)

        # Generate filename with datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./resources/icon_{timestamp}.png"

        # Save the image
        with open(filename, "wb") as f:
            f.write(image_response.content)

        # Upload the image to DigitalOcean Spaces
        file_url = upload_file_to_spaces(filename)

        if file_url:
            # Update the main_topic_collection with the new image URL
            updated = await update_main_topic_document(main_topic_id, {"link_image_icon": file_url})
            if not updated:
                raise ValueError("Failed to update main topic with new image URL")

        # Clean up the local file
        os.remove(filename)

        return file_url    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error generating image: {str(e)}")
