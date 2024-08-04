Smart Library AI Component
This README covers the AI component of the Smart Library project. The project is divided into two main parts: the backend (implemented with FastAPI) and the frontend (implemented with Streamlit).

Backend
The backend of the AI component is located in the smart-library folder and consists of several key modules.

Modules
Utils/prompt.py
This module contains the prompts used by various models in the project.

Common/AI/chatbot.py
This file contains the main logic of the chatbot agent using LangGraph. The chatbot supports five intents:

Book Recommendation: The user asks for a book recommendation related to a specific topic.
Book Description: The user searches for a book based on a description or topic.
Top K Books: The user requests the top K books in a specific genre.
Add Book: The user wants to add a book to the database and mentions 'add'.
Unclear Intent: The user's intent is not clear from the question.
We use a model to detect the intent. For intents 1 and 2, a model is also used to provide answers. For intents 3 and 4, we query the local database to save resources and ensure clear, structured results.

Schemas/chat.py
This module includes the Pydantic schemas needed for the chat API.

Routes/chat.py
This file defines the API routes for the chat functionalities.

Running the Backend
To start the backend server, you need to use Poetry. Navigate to the smart-library directory and run the following commands:

Install the dependencies:

poetry install
Start the server:

poetry run uvicorn app.app:app --reload

Frontend
The frontend is implemented using Streamlit and serves as the user interface for interacting with the chatbot.

app.py
The app.py file contains the Streamlit application code that provides the user interface to interact with the chatbot.

Running the Frontend
To start the Streamlit app, navigate to the directory containing app.py and run:

streamlit run app.py

File Descriptions
app.py
The main Streamlit application file that defines the user interface and interactions with the backend API.