from fastapi import FastAPI # type: ignore
from app.routes import users, books, authors, chat
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5500",  
    "http://127.0.0.1:5500",  
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(books.router)
app.include_router(authors.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Simple User API"}

@app.get("/health_check")
def health_check():
        return {"message": "API is running"}
