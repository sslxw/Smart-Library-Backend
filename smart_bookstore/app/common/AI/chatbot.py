import asyncio
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

embeddings = HuggingFaceEmbeddings()
db_chroma = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

model = ChatOpenAI(model="gpt-4o-mini", api_key="")
intent_model = ChatOpenAI(model="gpt-4o-mini", api_key="")

model = model.with_config(tags=["final_node"])

main_prompt = ChatPromptTemplate.from_template(main_template)
intent_prompt = ChatPromptTemplate.from_template(intent_template)

main_chain = main_prompt | model
intent_chain = intent_prompt | intent_model

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

def ensure_session_id(state):
    if 'session_id' not in state:
        state['session_id'] = 'default_session'
    return state

async def detect_intent(state):
    state = ensure_session_id(state)
    
    intent_input = state['messages'][-1].content
    intent_response = intent_chain.invoke([HumanMessage(content=intent_input)])
    intent = intent_response.content.strip().lower().split()[0]
    print(intent)
    if intent == "unknown":
        combined_input = f"The user's intent could not be recognized."
        final_response = await main_chain.ainvoke([HumanMessage(content=combined_input)])
        
        response_message = AIMessage(content=final_response.content)
        
        return {
            "messages": [response_message], "intent": "unknown", "session_id": state['session_id']}
    
    return {
        "intent": intent.strip('"'), "session_id": state['session_id'], "messages": state['messages'] }

async def book_recommendation(state):
    state = ensure_session_id(state)
    
    human_input = state['messages'][-1].content
    context = retrieve(human_input)
    combined_input = f"Context: {context}\n\nHuman Message: {human_input}"

    response = await main_chain.ainvoke([HumanMessage(content=combined_input)])
    
    response_message = response.content
    
    session_history = get_session_history(state['session_id'])
    session_history.add_user_message(human_input)  
    session_history.add_ai_message(response_message)  
        
    return {"messages": state['messages'] + [AIMessage(content=response_message)]}

async def top_books_genre(state, db: Session):
    state = ensure_session_id(state)
    
    message_content = state['messages'][-1].content.lower()
    print(f"Received message content: {message_content}")
    
    match = re.search(r"top (\d+) books in (.+)", message_content, re.IGNORECASE)
    if match:
        k = int(match.group(1))
        genre = match.group(2).strip()
        print(f"Querying top {k} books in the genre: {genre}")
        top_books = db.query(Book).filter(Book.genre.ilike(f"%{genre}%")).order_by(Book.average_rating.desc()).limit(k).all()
        if top_books:
            response_message = f"Here are the top {k} books in the genre '{genre}':\n\n"
            for i, book in enumerate(top_books, 1):
                response_message += f"{i}. \"{book.title}\" by {book.author.name} (Rating: {book.average_rating})\n"
        else:
            response_message = f"No books found in the genre '{genre}'."
    else:
        response_message = "Please specify the number of top books and the genre."
    
    combined_input = f"Human Message: {message_content}\n\n{response_message}"
    print(f"Combined input for model: {combined_input}")
    
    response = await main_chain.ainvoke([HumanMessage(content=combined_input)]) # change this later
    
    response_message = response.content

    session_history = get_session_history(state['session_id'])
    session_history.add_user_message(message_content)  
    session_history.add_ai_message(response_message)  
    
    return {"messages": state['messages'] + [AIMessage(content=response_message)], "session_id": state['session_id']}

async def top_books_author(state, db: Session):
    state = ensure_session_id(state)
    
    message_content = state['messages'][-1].content.lower()
    print(f"Received message content: {message_content}")
    
    match = re.search(r"top (\d+) books by (.+)", message_content, re.IGNORECASE)
    if match:
        k = int(match.group(1))
        author_name = match.group(2).strip()
        print(f"Querying top {k} books by the author: {author_name}")
        author = db.query(Author).filter(Author.name.ilike(f"%{author_name}%")).first()
        if author:
            top_books = db.query(Book).filter(Book.author_id == author.author_id).order_by(Book.average_rating.desc()).limit(k).all()
            if top_books:
                response_message = f"Here are the top {k} books by '{author_name}':\n\n"
                for i, book in enumerate(top_books, 1):
                    response_message += f"{i}. \"{book.title}\" (Rating: {book.average_rating})\n"
            else:
                response_message = f"No books found by the author '{author_name}'."
        else:
            response_message = f"Author '{author_name}' does not exist in the database."
    else:
        response_message = "Please specify the number of top books and the author."

    combined_input = f"Human Message: {message_content}\n\n{response_message}"
    print(f"Combined input for model: {combined_input}")
    
    response = await main_chain.ainvoke([HumanMessage(content=combined_input)])
    
    response_message = response.content

    session_history = get_session_history(state['session_id'])
    session_history.add_user_message(message_content)  
    session_history.add_ai_message(response_message)  

    return {"messages": state['messages'] + [AIMessage(content=response_message)], "session_id": state['session_id']}

async def add_book(state, db: Session):
    state = ensure_session_id(state)
    
    message_content = state['messages'][-1].content

    match = re.search(
        r'add book titled "(.+?)" by (.+?), genre: (.+?), description: (.+?), rating: (\d+(\.\d+)?), published in (\d{4})',message_content, re.IGNORECASE)
    
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
    
    combined_input = f"User requested to add a book:\n\n{message_content}\n\n{response_content}"

    final_response = await main_chain.ainvoke([HumanMessage(content=combined_input)])
    
    response_message = final_response.content

    session_history = get_session_history(state['session_id'])
    session_history.add_user_message(message_content)  
    session_history.add_ai_message(response_message)  
        
    return {"messages": state['messages'] + [AIMessage(content=final_response.content)]}

async def chat_history_query(state):
    state = ensure_session_id(state)
    
    query = state['messages'][-1].content
    history = get_session_history(state['session_id']).messages
    combined_history = "\n".join([f"Human: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}" for msg in history])
    print(combined_history)
    combined_input = f"History:\n{combined_history}\n\nHuman Message: {query}"

    config = {"configurable": {"session_id": state['session_id']}}

    response = await main_chain.ainvoke([HumanMessage(content=combined_input)], config=config)
    
    response_message = response.content
    return {"messages": state['messages'] + [AIMessage(content=response_message)], "session_id": state['session_id'], "session_history": state.get('session_history', [])}

async def greet(state):
    state = ensure_session_id(state)
    
    human_input = state['messages'][-1].content
    combined_input = f"Human Message: {human_input} + (Only greet the user)" # play around with this later
    config = {"configurable": {"session_id": state['session_id']}}

    response = await main_chain.ainvoke([HumanMessage(content=combined_input)], config=config)
    
    response_message = response.content
        
    return {"messages": state['messages'] + [AIMessage(content=response_message)]}

workflow = StateGraph(AgentState)

workflow.add_node("detect_intent", detect_intent)
workflow.add_node("book_recommendation", book_recommendation)

def top_books_genre_node(state):
    with next(get_db()) as db:
        return asyncio.run(top_books_genre(state, db))

def top_books_author_node(state):
    with next(get_db()) as db:
        return asyncio.run(top_books_author(state, db))

def add_book_node(state):
    with next(get_db()) as db:
        return asyncio.run(add_book(state, db))

workflow.add_node("top_books_genre", top_books_genre_node)
workflow.add_node("top_books_author", top_books_author_node)
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
        "top_books_author": "top_books_author",
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

