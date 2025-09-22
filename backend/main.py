from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.chat_routs import chat
from routes.auth_routes import auth
from routes.students_routes import students_router
from config.database import get_db
load_dotenv()



app = FastAPI(
    title="Login and Agent Management API",
    description="API for managing user logins and agent information",
    version="1.0.0",
    docs_url="/docs",          
    redoc_url="/redoc"         
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat, prefix="/chat", tags=["chat"])
app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(students_router, prefix="", tags=["students"])



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

