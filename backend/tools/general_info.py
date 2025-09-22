
# LangChain/Groq for RAG
from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.memory import ConversationBufferWindowMemory
from agents import function_tool
from dotenv import load_dotenv
import os
    
# ------------------ Load environment ------------------
load_dotenv()


# ------------------ Initialize Groq LLM for RAG ------------------
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables!")

groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
    temperature=0.7,
    max_tokens=1024
)

memory = ConversationBufferWindowMemory(k=5)

# ------------------ Load & Split PDF/Text Documents ------------------
def load_documents(file_path: str = r"university.txt", chunk_size: int = 500, chunk_overlap: int = 100):
    try:
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        split_docs = splitter.split_documents(documents)
        return split_docs
    except Exception as e:
        print("Error loading documents:", e)
        return []

split_docs = load_documents()

# ------------------ RAG Tool ------------------
@function_tool
def rag_query(user_question: str):
    """
    Answer questions based on provided PDF/text documents using RAG.
    """
    print("RAG Tool Invoked")

    if not user_question.strip():
        return {"Data": {}, "Error": True, "Message": "User question cannot be empty."}

    if user_question.lower() in ["hi", "hello", "hey"]:
        return {"Data": {}, "Error": False, "Message": "Hello! How can I assist you today?"}

    try:
        if not split_docs:
            return {"Data": {}, "Error": True, "Message": "No documents have been loaded for querying."}

        # ⚡ Consider retrieving only top-k relevant chunks
        context_text = "\n\n".join([doc.page_content for doc in split_docs][:10])

        prompt = (
            f"You are a helpful assistant. Answer the user's question based on the following context.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {user_question}\n\n"
            f"Answer concisely and clearly."
        )

        response = groq_llm.invoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)

        return {
            "Data": {"used_chunks": min(10, len(split_docs))},
            "Error": False,
            "Message": answer
        }

    except Exception as e:
        return {"Data": {}, "Error": True, "Message": f"Error querying documents: {e}"}

