from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import re
from app.common.database.database import get_db
from app.schemas.chat import AgentState
from app.common.database.models import Book, Author
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_ollama.llms import OllamaLLM
from app.utils.prompts import main_template, intent_template

# Initialize embeddings and Chroma
embeddings = HuggingFaceEmbeddings()
db_chroma = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# Initialize models
model = ChatOpenAI(model="gpt-4o-mini", api_key="API-KEY")
intent_model = ChatOpenAI(model="gpt-4o-mini", api_key="API-KEY")

# Initialize prompts
main_prompt = ChatPromptTemplate.from_template(main_template)
intent_prompt = ChatPromptTemplate.from_template(intent_template)

main_chain = main_prompt | model
intent_chain = intent_prompt | intent_model

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

main_with_message_history = RunnableWithMessageHistory(
    runnable=main_chain,
    get_session_history=get_session_history
)

intent_with_message_history = RunnableWithMessageHistory(
    runnable=intent_chain,
    get_session_history=get_session_history
)

def ensure_session_id(state):
    if 'session_id' not in state:
        state['session_id'] = 'default_session'
    return state

def detect_intent(state):
    state = ensure_session_id(state)
    
    intent_input = state['messages'][-1].content
    config = {"configurable": {"session_id": state['session_id']}}
    intent_response = intent_with_message_history.invoke([HumanMessage(content=intent_input)], config=config)
    intent = intent_response.content.strip().lower().split()[0]
    if intent == "unknown":
        response = AIMessage(content="I'm sorry, I can only answer questions that relate to book recommendations, finding books that relate to a description, top books in a specific genre, or adding a book to the database.")
        return {"messages": [response], "intent": "unknown", "session_id": state['session_id']}
    return {"intent": intent.strip('"'), "session_id": state['session_id'], "messages": state['messages']}

def book_recommendation(state):
    state = ensure_session_id(state)
    
    human_input = state['messages'][-1].content
    context = retrieve(human_input)
    combined_input = f"Context: {context}\n\nHuman Message: {human_input}"

    config = {"configurable": {"session_id": state['session_id']}}
    response = main_with_message_history.invoke([HumanMessage(content=combined_input)], config=config)
    
    response_message = response.content
    
    # Store the book recommendation in the session history
    state['session_history'] = state.get('session_history', [])
    state['session_history'].append({'type': 'book_recommendation', 'content': response_message})
    
    return {"messages": state['messages'] + [AIMessage(content=response_message)], "session_id": state['session_id'], "session_history": state['session_history']}

def top_books_genre(state, db: Session):
    state = ensure_session_id(state)
    
    message_content = state['messages'][-1].content.lower()
    match = re.search(r"top (\d+) books in (.+)", message_content, re.IGNORECASE)
    if match:
        k = int(match.group(1))
        genre = match.group(2).strip()
        top_books = db.query(Book).filter(Book.genre.ilike(f"%{genre}%")).order_by(Book.average_rating.desc()).limit(k).all()
        if top_books:
            response_content = f"Here are the top {k} books in the genre '{genre}':\n"
            for book in top_books:
                response_content += f"- {book.title} by {book.author.name} (Rating: {book.average_rating})\n"
        else:
            response_content = f"No books found in the genre '{genre}'."
        response = AIMessage(content=response_content)
    else:
        response = AIMessage(content="Please specify the number of top books and the genre.")
    
    # Store the top books genre response in the session history
    state['session_history'] = state.get('session_history', [])
    state['session_history'].append({'type': 'top_books_genre', 'content': response.content})
    
    return {"messages": state['messages'] + [response], "session_id": state['session_id'], "session_history": state['session_history']}

def add_book(state, db: Session):
    state = ensure_session_id(state)
    
    message_content = state['messages'][-1].content

    match = re.search(
        r'add book titled "(.+?)" by (.+?), genre: (.+?), description: (.+?), rating: (\d+(\.\d+)?), published in (\d{4})',
        message_content, re.IGNORECASE
    )
    
    print(f"Message Content: {message_content}")
    print(f"Match: {match.groups() if match else 'No match found'}")
    
    if match:
        title, author_name, genre, description, average_rating, _, published_year = match.groups()
        
        author = db.query(Author).filter(Author.name.ilike(author_name.strip())).first()
        
        if author:
            new_book = Book(
                title=title,
                author_id=author.author_id,  
                genre=genre,
                description=description,
                average_rating=float(average_rating),
                published_year=int(published_year)
            )
            db.add(new_book)
            db.commit()
            response_content = f"Book '{title}' by {author_name} added successfully."
        else:
            response_content = f"Author '{author_name}' does not exist in the database. Please add the author first."
    else:
        response_content = (
            "Please provide all the required information: "
            'title, author, genre, description, rating, and published year. '
            'The correct format is: add book titled "BOOK_TITLE" by AUTHOR_NAME, genre: GENRE, '
            'description: DESCRIPTION, rating: RATING, published in YEAR.'
        )
    
    response = AIMessage(content=response_content)
    
    # Store the add book response in the session history
    state['session_history'] = state.get('session_history', [])
    state['session_history'].append({'type': 'add_book', 'content': response.content})
    
    return {"messages": state['messages'] + [response], "session_id": state['session_id'], "session_history": state['session_history']}

def chat_history_query(state):
    state = ensure_session_id(state)
    
    query = state['messages'][-1].content
    history = get_session_history(state['session_id']).messages
    combined_history = "\n".join([f"Human: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}" for msg in history])
    
    combined_input = f"History:\n{combined_history}\n\nHuman Message: {query}"

    config = {"configurable": {"session_id": state['session_id']}}
    response = main_with_message_history.invoke([HumanMessage(content=combined_input)], config=config)
    
    response_message = response.content
    return {"messages": state['messages'] + [AIMessage(content=response_message)], "session_id": state['session_id'], "session_history": state.get('session_history', [])}

def greet(state):
    state = ensure_session_id(state)
    
    response = AIMessage(content="Hello! How can I assist you today?")
    return {"messages": state['messages'] + [response], "session_id": state['session_id'], "session_history": state.get('session_history', [])}

# Define the workflow
workflow = StateGraph(AgentState)

workflow.add_node("detect_intent", detect_intent)
workflow.add_node("book_recommendation", book_recommendation)

def top_books_genre_node(state):
    with next(get_db()) as db:
        return top_books_genre(state, db)

def add_book_node(state):
    with next(get_db()) as db:
        return add_book(state, db)

workflow.add_node("top_books_genre", top_books_genre_node)
workflow.add_node("add_book", add_book_node)
workflow.add_node("chat_history_query", chat_history_query)
workflow.add_node("greet", greet)

workflow.set_entry_point("detect_intent")

workflow.add_conditional_edges(
    "detect_intent",
    lambda state: state["intent"],
    {
        "book_recommendation": "book_recommendation",
        "top_books_genre": "top_books_genre",
        "add_book": "add_book",
        "chat_history_query": "chat_history_query",
        "greet": "greet",
        "unknown": END,
    }
)

app_graph = workflow.compile()

def retrieve(query):
    docs = db_chroma.similarity_search(query)
    retrieved_docs = [doc.page_content for doc in docs]
    return retrieved_docs
