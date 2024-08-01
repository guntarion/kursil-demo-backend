import os
from docx import Document
from docx.shared import Inches
from bson import ObjectId
from docx.enum.style import WD_STYLE_TYPE
from markdown import markdown
from bs4 import BeautifulSoup
from ..db.operations import main_topic_collection, list_topics_collection, points_discussion_collection

async def get_all_handouts_by_main_topic_id(main_topic_id: str):
    # Get the main topic document
    main_topic = await main_topic_collection.find_one({"_id": ObjectId(main_topic_id)})
    if not main_topic:
        return []

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

    return all_handouts

async def generate_word_document(handouts):
    doc = Document()
    doc.add_heading('Handouts Document', 0)

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

    # Ensure the documents directory exists
    os.makedirs('./documents', exist_ok=True)
    document_path = './documents/handouts_document.docx'
    doc.save(document_path)
    return document_path