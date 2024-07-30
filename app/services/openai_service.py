# fastapi app/services/openai_service.py
import asyncio
from bson import ObjectId
import os
import re
from openai import OpenAI
from typing import List, Dict
from dotenv import load_dotenv
import tiktoken
from app.services.cost_calculator import calculate_cost
from app.db.database import main_topic_collection, list_topics_collection
from app.db.operations import get_topic_by_name, add_elaborated_point

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
        "main_topic_objective": summary
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

def elaborate_discussionpoint(topic: str, objective: str, points_of_discussion: List[str]) -> List[Dict[str, str]]:
    prompt_template = read_prompt("./app/prompts/prompt_detaillistof_discussionpoint.txt")

    points_str = "\n".join([f"  - {point}" for point in points_of_discussion])
    prompt = prompt_template.format(topic=topic, objective=objective, pointsofdiscussion=points_str)

    messages = [
        {"role": "system", "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    elaborated_content = completion.choices[0].message.content.strip()
    # print("\n\nelaborated_content", elaborated_content)

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

    # logger.debug(f"Parsed result: {elaborated_points}")

    # Store elaborated points in the database
    topic_doc = get_topic_by_name(topic)
    if topic_doc:
        topic_id = topic_doc['_id']
        # print("🚀 ~ topic_id:", topic_id)
        for point in elaborated_points:
            add_elaborated_point(point['subtopic'], point['elaboration'], topic_id)

    return elaborated_points

async def generate_prompting_and_content(elaborated_points: List[Dict[str, str]], topic: str) -> List[Dict[str, str]]:
    prompt_template = read_prompt("./app/prompts/prompt_create_prompttowrite.txt")
    results = []

    for point in elaborated_points:
        point_of_discussion = point['point_of_discussion']
        elaboration = point['elaboration']
        
        prompt = prompt_template.replace("{point_of_discussion}", point_of_discussion)
        prompt = prompt.replace("{elaboration}", elaboration)

        messages = [
            {"role": "system", "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
            {"role": "user", "content": prompt}
        ]

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        prompting_summary = completion.choices[0].message.content.strip()
        
        # Generate content using the prompting summary
        content = await generate_content(prompting_summary, point_of_discussion)
        
        results.append({
            "point_of_discussion": point_of_discussion,
            "prompting": prompting_summary,
            "content": content
        })
        
        # Provide progress update
        print(f"Finished creating content for '{point_of_discussion}'")
        
        # Add a delay between requests
        await asyncio.sleep(2)  # 2-second delay

    return results

async def generate_content(prompting: str, point_of_discussion: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields. Create a detailed and comprehensive section for a book chapter that addresses the provided discussion points. The content should be tailored for PLN Persero employees who have diverse educational backgrounds, ensuring that the explanations are technically informative yet understandable for non-technical staff. The aim of this book chapter is to provide PLN Persero employees with a well-rounded understanding of the provided discussion points."
        },
        {
            "role": "user",
            "content": prompting
        }
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    content = completion.choices[0].message.content
    print(f"Generated content for '{point_of_discussion}'")
    return content

# Individual functions to generate prompting
def generate_prompting(elaboration: str, point_of_discussion: str) -> str:
    prompt_template = read_prompt("./app/prompts/prompt_create_prompttowrite.txt")
    
    prompt = prompt_template.replace("{point_of_discussion}", point_of_discussion)
    prompt = prompt.replace("{elaboration}", elaboration)

    messages = [
        {"role": "system", "content": "You are an educational content developer and are a consultant for PLN Pusdiklat (education and training centre) which supports Perusahaan Listrik Negara (PLN) in running the electricity business and other related fields."},
        {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return completion.choices[0].message.content.strip()

def generate_handout(point_of_discussion: str, prompting: str) -> str:
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

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return completion.choices[0].message.content.strip()