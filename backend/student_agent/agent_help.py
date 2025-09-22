from agents import Agent, OpenAIChatCompletionsModel, ModelSettings, Runner  # type: ignore
from openai import AsyncOpenAI  # type: ignore
from tools.crud_tool import  add_student,read_students, update_student, delete_student,read_student_by_id
from tools.general_info import rag_query
from dotenv import load_dotenv
import os

openai_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
triage_agent = Agent(
    name="Student Record Management Agent",
    instructions="""
You are an AI assistant that helps manage student records. You can perform the following actions:
1. Add a new student record.
2. Read existing student records.
3. Update student records.
4. Delete student records.
5. Answer general questions about students using the RAG tool.
    """,
    model=OpenAIChatCompletionsModel(
        model="gemini-2.5-flash",
        openai_client=openai_client
    ),
    tools=[read_students, add_student, delete_student, update_student, read_student_by_id, rag_query],
    model_settings=ModelSettings(temperature=0.7, max_tokens=1000),
)