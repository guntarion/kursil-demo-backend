# app/services/openai_service.py
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


def parse_generated_content(content):
    sections = content.split('\n\n')
    topics = []
    topic_pattern = re.compile(
        r'\d+\.\s+\*\*Topic Title:\*\* (.*?)\n', re.DOTALL)
    objective_pattern = re.compile(r'- \*\*Objective:\*\* (.*?)\n', re.DOTALL)
    key_concepts_pattern = re.compile(
        r'- \*\*Key Concepts:\*\* (.*?)\n', re.DOTALL)
    skills_pattern = re.compile(
        r'- \*\*Skills to be Mastered:\*\* (.*?)\n', re.DOTALL)
    discussion_pattern = re.compile(
        r'- \*\*Point of Discussion:\*\*\n(.*?)(?=\n\s*\n|\Z)', re.DOTALL)

    topics = topic_pattern.findall(content)
    objectives = objective_pattern.findall(content)
    key_concepts = key_concepts_pattern.findall(content)
    skills = skills_pattern.findall(content)
    discussions = discussion_pattern.findall(content)

    if not (len(topics) == len(objectives) == len(key_concepts) == len(skills) == len(discussions)):
        raise ValueError("Mismatch in the number of extracted items.")

    parsed_topics = []

    for i, topic in enumerate(topics):
        discussion_points = discussions[i].strip().split('\n')
        discussion_points = [point.strip('- ').strip()
                             for point in discussion_points]

        parsed_topics.append({
            "topic_name": topic.strip(),
            "objective": objectives[i].strip(),
            "key_concepts": key_concepts[i].strip(),
            "skills_to_be_mastered": skills[i].strip(),
            "point_of_discussion": discussion_points
        })

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

    # Save to MongoDB
    main_topic_data = {
        "main_topic": topic,
        "cost": total_cost_idr,
        "list_of_topics": [t["topic_name"] for t in parsed_topics]
    }
    result = main_topic_collection.insert_one(main_topic_data)
    main_topic_id = str(result.inserted_id)

    for topic in parsed_topics:
        topic["main_topic_id"] = main_topic_id
        list_topics_collection.insert_one(topic)

    return {"main_topic_id": main_topic_id, "cost": total_cost_idr}


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def parse_and_save_topics(main_topic, text):
    parsed_topics = parse_generated_content(text)

    main_topic_data = {
        "main_topic": main_topic,
        "list_of_topics": [t["topic_name"] for t in parsed_topics]
    }

    result = main_topic_collection.insert_one(main_topic_data)
    main_topic_id = str(result.inserted_id)

    for topic in parsed_topics:
        topic["main_topic_id"] = main_topic_id
        list_topics_collection.insert_one(topic)

    return {"main_topic_id": main_topic_id}


def save_topic_to_database():
    file_path = "1_listof_topic.txt"
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    content = read_file(file_path)
    # This can be obtained from request or other means
    main_topic = "Digital Marketing"
    result = parse_and_save_topics(main_topic, content)

    print("Topics saved to database successfully")
    return result
