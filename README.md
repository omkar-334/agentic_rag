# Agentic RAG Chatbot

## Introduction

The Agentic RAG Chatbot is a sophisticated AI-powered application that combines Retrieval-Augmented Generation (RAG) with an agent-based approach to provide intelligent responses to user queries. This chatbot is designed to assist with educational content across various grades, subjects, and chapters.

### Key Features

1. **Grade-Subject-Chapter Based Queries**: Users can specify the grade, subject, and chapter for their questions, allowing for targeted and relevant responses.
2. **Translation & Text-to-Speech**: Powered by Sarvam APIs.
3. **Debugging Interface**: A built-in debugging modal for monitoring agent logs.

### Architecture

The application uses a FastAPI backend which integrates with a Gradio frontend for an interactive user interface. The core logic is handled by custom agent and retriever functions, powered by Groq LLM and Qdrant Vector Database. PDF preprocessing is done using PyMuPDF and data validation using Pydantic.  

<div align="center">
 <img src="https://avatars.githubusercontent.com/u/1525981?s=200&v=4" height="40" width="43" alt="python logo"/> &nbsp;&nbsp;
<img src="https://avatars.githubusercontent.com/u/156354296?s=200&v=4" height="40" width="43" alt="fastapi logo"/>&nbsp;&nbsp;
<img src="https://avatars.githubusercontent.com/u/110818415?s=48&v=4" height="40" width="43" alt="fastapi logo"/>&nbsp;&nbsp;
<img src="https://avatars.githubusercontent.com/u/73504361?s=200&v=4" height="40" width="43" alt="fastapi logo"/>&nbsp;&nbsp;
<img src="https://avatars.githubusercontent.com/u/7464134?s=200&v=4" height="40" width="43" alt="fastapi logo"/>&nbsp;&nbsp;
<img src="https://avatars.githubusercontent.com/u/51063788?s=48&v=4" height="40" width="43" alt="fastapi logo"/>&nbsp;&nbsp;
<img src="https://avatars.githubusercontent.com/u/48152365?s=48&v=4" height="40" width="43" alt="fastapi logo"/>
</div>

## Endpoints

The API provides the following endpoints:

1. **GET /status**
   - Description: Check the status of the API and available endpoints.
   - Response: JSON object with status and list of endpoints.

2. **GET /agent**
   - Description: Process a query using the agent-based approach.
   - Parameters: 
     - query: str
     - grade: str
     - subject: str
     - chapter: str
   - Response: Agent's response.

3. **GET /rag**
   - Description: Retrieval Augmented Generation.
   - Parameters: 
     - query: str
     - grade: str
     - subject: str
     - chapter: str
   - Response: RAG response.

4. **GET /translate**
   - Description: Translate text from one language to another.
   - Parameters:
     - text: str
     - src: str (source language)
     - dest: str (destination language)
   - Response: Translated text.

5. **GET /tts**
   - Description: Convert text to speech.
   - Parameters:
     - text: str
     - src: str (source language)
   - Response: Audio data (.wav, base64 encoded).

## Agent Tools

The chatbot utilizes several agent tools to process and respond to queries:

1. **function_caller**:   
    - Main agent function for processing queries and taking decisions.
    ![Function Caller](https://raw.githubusercontent.com/omkar-334/agentic_rag/main/images/function_caller.png)

2. **retriever**: 
   - Purpose: Retrieve relevant information from the vector database.
   - The Agent decides whether to retrieve or not, based on the relevance of the user's prompt and if it's related to the educational database.
   ![Retriever](https://raw.githubusercontent.com/omkar-334/agentic_rag/main/images/retreiver.png)

3. **translator**: 
   - Purpose: Translate text between languages.
   - Activate it by asking the chatbot to translate to a specific language.
   ![Translator](https://raw.githubusercontent.com/omkar-334/agentic_rag/main/images/translator.png)

4. **speaker**: 
   - Purpose: Convert text to speech.
   - Activate it by asking the chatbot to read aloud or convert to audio.
   ![Speaker](https://raw.githubusercontent.com/omkar-334/agentic_rag/main/images/tts.png)

5. **extractor**
   - Purpose: Extracts text content from website URLs.
   - Activate it by providing a URL and specifying a task like summarization.
   ![Extractor](https://raw.githubusercontent.com/omkar-334/agentic_rag/main/images/extractor.png)

6. **Agent Debug Logs**
   - The Agent's decisions and logs are visible in a modal below the messagebox.
    - Click on the terminal icon in the upper-right corner to show it.
   ![Debug](https://raw.githubusercontent.com/omkar-334/agentic_rag/main/images/debuglog.png)

These tools work together to provide a comprehensive and interactive chatbot experience, capable of understanding context, retrieving relevant information, and presenting it in various formats to the user.
