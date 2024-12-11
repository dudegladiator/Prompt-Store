from typing import Dict, List
from pinecone import Pinecone, ServerlessSpec
from utils.config import settings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from utils.app_logger import setup_logger
from langchain_google_genai import GoogleGenerativeAIEmbeddings


pc = Pinecone(api_key=settings.PINECONE_API_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GEMINI_API_KEY)
index = pc.Index("nm1")

logger = setup_logger("src/llm/pinecone.py")

def create_index(name: str, dimension: int = 768):
    logger.info(f"Creating index: {name} with dimension: {dimension}")
    try:
        pc.create_index(name, dimension, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
        index = pc.Index(name)
        logger.info(f"Successfully created index: {name}")
        return index
    except Exception as e:
        logger.error(f"Error creating index {name}: {str(e)}")
        return None
    
def delete_index(name: str):
    logger.info(f"Deleting index: {name}")
    try:
        pc.delete_index(name)
        logger.info(f"Successfully deleted index: {name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting index {name}: {str(e)}")
        return False

def upload_documents(tenant_id: str, documents: List[Document], uuids: List[str]):
    logger.info(f"Uploading {len(documents)} documents for tenant_id: {tenant_id}")
    try:
        vector_store = PineconeVectorStore(index=index, embedding=embeddings, namespace=tenant_id)
        data = vector_store.add_documents(documents=documents, ids=uuids)
        logger.info(f"Successfully uploaded {len(documents)} documents for tenant_id: {tenant_id}")
        return data
    except Exception as e:
        logger.error(f"Error uploading documents for tenant_id {tenant_id}: {str(e)}")
        return None
    
def delete_documents(tenant_id: str, integration_id: str, uuids: List[str]):
    logger.info(f"Deleting {len(uuids)} documents for tenant_id: {tenant_id} and integration_id: {integration_id}")
    try:
        vector_store = PineconeVectorStore(index=index, embedding=embeddings, namespace=tenant_id)
        data = vector_store.delete(ids=uuids)
        logger.info(f"Successfully deleted {len(uuids)} documents for tenant_id: {tenant_id} and integration_id: {integration_id}")
        return data
    except Exception as e:
        logger.error(f"Error deleting documents for tenant_id {tenant_id} and integration_id: {integration_id}: {str(e)}")
        return None
    
def retrieve_documents(tenant_id: str, query: Document, filters: Dict = None, top_k: int = 5):
    logger.info(f"Retrieving documents for tenant_id: {tenant_id}, query: {query}, top_k: {top_k}")
    try:
        vector_store = PineconeVectorStore(index=index, embedding=embeddings, namespace=tenant_id)
        data = vector_store.similarity_search(query=query, k=top_k, filter=filters)
        logger.info(f"Successfully retrieved {len(data)} documents for tenant_id: {tenant_id}")
        return data
    except Exception as e:
        logger.error(f"Error retrieving documents for tenant_id {tenant_id}: {str(e)}")
        return None