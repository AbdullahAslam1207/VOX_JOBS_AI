from langchain_community.document_loaders import JSONLoader
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import json
import os
from uuid import uuid4

# Path to your JSON file
JSON_PATH = "Scraped_Data/all_jobs_data.json"
CHROMA_DB_DIR = "vector_store/all_jobs_db"

def create_chroma_db_from_jobs():
    # 1️⃣ Load the JSON data
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)

        # 2️⃣ Convert each job entry into a Document
        docs = []
        for job in jobs_data:
            # Create a meaningful text representation for embedding
            content = f"""
            Job Title: {job.get('title', '')}
            Company: {job.get('company_name', '')}
            Location: {job.get('location', '')}
            City: {job.get('city', '')}
            Job Type: {job.get('job_type', '')}
            Education: {job.get('education', '')}
            Experience: {job.get('experience', '')}
            Posted Date: {job.get('posted_date', '')}
            Apply Before: {job.get('apply_before', '')}
            Job Description: {job.get('job_description', '')}
            Skills: {job.get('skills', '')}
            Source: {job.get('job_source', '')}
            """
            docs.append(
                Document(
                    page_content=content.strip(),
                    metadata={
                        "id": job.get("id"),
                        "title": job.get("title"),
                        "company_name": job.get("company_name"),
                        "location": job.get("location"),
                        "city": job.get("city"),
                        "source_city": job.get("source_city"),
                        "job_link": job.get("job_link"),
                        "job_source": job.get("job_source"),
                        "education": job.get("education"),
                        "experience": job.get("experience"),
                    },
                )
            )
        uuids = [str(uuid4()) for _ in range(len(docs))]
        # 3️⃣ Initialize MiniLM embeddings
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # 4️⃣ Create (or overwrite) Chroma vector store
        if os.path.exists(CHROMA_DB_DIR):
            print("🧹 Existing Chroma DB found, deleting it...")
            import shutil
            shutil.rmtree(CHROMA_DB_DIR)

        print("⚙️ Creating embeddings and storing in Chroma DB...")
        vector_store = Chroma(
        collection_name="jobs_collection",
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_DIR,
        )
        vector_store.add_documents(documents=docs, ids=uuids)
        print(f"✅ Stored {len(docs)} job documents in Chroma DB at '{CHROMA_DB_DIR}'")
        return {"status": "success", "message": f"Stored {len(docs)} job documents in Chroma DB."}
    except Exception as e:
        print(f"❌ Error creating Chroma DB: {e}")
        return {"status": "error", "message": str(e)}

