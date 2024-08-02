import os
import re
from docx import Document
from docx.shared import Inches
from bson import ObjectId
from docx.enum.style import WD_STYLE_TYPE
from markdown import markdown
from bs4 import BeautifulSoup
from datetime import datetime
from ..db.operations import main_topic_collection, list_topics_collection, points_discussion_collection

async def get_all_handouts_by_main_topic_id(main_topic_id: str):
    # Get the main topic document
    main_topic = await main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})
    if not main_topic:
        return None, []

    all_handouts = []

    # Iterate through list_of_topics
    for topic_name in main_topic['list_of_topics']:
        # Find the corresponding document in list_topics_collection
        list_topic = await list_topics_collection.find_one({"topic_name": topic_name})
        if not list_topic:
            continue

        # Get all points_discussion documents for this topic
        points_discussion_cursor = points_discussion_collection.find({
            "topic_name_id": list_topic['_id']
        })
        points_discussion_docs = await points_discussion_cursor.to_list(length=None)

        # Collect non-empty handouts
        for point in points_discussion_docs:
            if point.get('handout'):
                all_handouts.append({
                    'topic_name': topic_name,
                    'point_of_discussion': point['point_of_discussion'],
                    'handout': point['handout']
                })

    return main_topic['main_topic'], all_handouts

def sanitize_filename(filename):
    """Remove or replace characters that are unsafe for filenames."""
    # Replace spaces and other unsafe characters with underscores
    filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    # Replace multiple spaces with a single underscore
    filename = re.sub(r'\s+', '_', filename)
    return filename


async def generate_handout_word_document(main_topic: str, handouts: list):
    doc = Document()
    doc.add_heading('Handouts Document', 0)
    print("main_topic === ", main_topic)
    # Get existing styles
    styles = doc.styles

    for handout in handouts:
        doc.add_heading(handout['topic_name'], level=1)
        doc.add_heading(handout['point_of_discussion'], level=2)
        
        # Convert markdown to HTML
        html = markdown(handout['handout'])
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        for element in soup.find_all():
            if element.name == 'h4':
                doc.add_paragraph(element.text, style='Heading 3')
            elif element.name == 'p':
                paragraph = doc.add_paragraph()
                for child in element.children:
                    if child.name == 'strong':
                        paragraph.add_run(child.text).bold = True
                    else:
                        paragraph.add_run(child.text)
            elif element.name == 'ul':
                for li in element.find_all('li'):
                    doc.add_paragraph(li.text, style='List Bullet')

        doc.add_page_break()

    # Generate filename
    date_str = datetime.now().strftime("%y-%m-%d")
    sanitized_topic = sanitize_filename(main_topic)
    base_filename = f"{sanitized_topic} - {date_str} - handout"

    # Ensure the documents directory exists
    os.makedirs('./documents', exist_ok=True)

    # Check for existing files and append number if necessary
    index = 0
    while True:
        if index == 0:
            filename = f"{base_filename}.docx"
        else:
            filename = f"{base_filename} ({index}).docx"

        document_path = os.path.join('./documents', filename)
        if not os.path.exists(document_path):
            break
        index += 1

    doc.save(document_path)
    return document_path