# app/services/rag_service.py

import os
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAI
from langchain.chains import RetrievalQA
from .document_service import get_all_handouts_by_main_topic_id

# Load environment variables
load_dotenv()


async def ingest_data(main_topic_id: str):
    # 1. Get all handouts from the database
    main_topic, all_handouts = await get_all_handouts_by_main_topic_id(main_topic_id)

    if not all_handouts:
        return f"No handouts found for main topic: {main_topic}"

    # 2. Prepare documents for ingestion
    documents = []
    for handout in all_handouts:
        doc = f"Topic: {handout['topic_name']}\nPoint of Discussion: {handout['point_of_discussion']}\n\n{handout['handout']}"
        documents.append(doc)

    # 3. Split the text into chunks
    text_splitter = CharacterTextSplitter(
        chunk_size=1000, chunk_overlap=20, length_function=len)
    texts = text_splitter.split_text("\n\n".join(documents))

    # 4. Create embeddings and store them in FAISS
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts, embeddings)

    # 5. Save the FAISS index
    index_path = f"faiss_index_{main_topic_id}"
    vectorstore.save_local(index_path)

    return f"Data ingestion complete. FAISS index saved for main topic: {main_topic}"


async def load_qa_chain(main_topic_id: str):
    # 1. Load the saved FAISS index
    embeddings = OpenAIEmbeddings()
    index_path = f"faiss_index_{main_topic_id}"
    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    # 2. Create a retrieval-based QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

    return qa_chain


async def query_data(main_topic_id: str, query: str):
    qa_chain = await load_qa_chain(main_topic_id)
    response = await qa_chain.ainvoke({"query": query})
    return response["result"]
