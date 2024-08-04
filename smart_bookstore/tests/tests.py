import streamlit as st
import requests

# Define the backend URL
backend_url = "http://localhost:8000/chat"

st.title("Langchain Chatbot")

query = st.text_input("Ask me anything about books and authors:")
if st.button("Send"):
    response = requests.post(backend_url, json={"query": query})
    if response.status_code == 200:
        st.write(response.json().get("response"))
    else:
        st.write("Error:", response.status_code, response.text)
