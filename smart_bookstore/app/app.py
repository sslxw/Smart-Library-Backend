from fastapi import FastAPI # type: ignore
from app.routes import users, books, authors

app = FastAPI()

app.include_router(users.router)
app.include_router(books.router)
app.include_router(authors.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Simple User API"}

@app.get("/health_check")
def health_check():
        return {"message": "API is running"}
