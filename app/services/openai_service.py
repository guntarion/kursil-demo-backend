# fastapi app/services/openai_service.py
from bson import ObjectId
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
from app.services.cost_calculator import calculate_cost
from app.db.database import main_topic_collection, list_topics_collection

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

