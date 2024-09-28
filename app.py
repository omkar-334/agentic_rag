import base64
import tempfile

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import function_caller, retriever
from client import HybridClient
from sarvam import speaker, translator

app = FastAPI()
hclient = HybridClient()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatQuery(BaseModel):
    query: str
    grade: str
    subject: str
    chapter: str


class TranslateQuery(BaseModel):
    text: str
    src: str
    dest: str


class TTSQuery(BaseModel):
    text: str
    src: str


@app.get("/agent")
async def agent(query: ChatQuery):
    collection = f"{grade}_{subject.lower()}_{chapter}"
    return await function_caller(query.query, collection, hclient)


@app.get("/rag")
async def rag(query: ChatQuery):
    collection = f"{grade}_{subject.lower()}_{chapter}"
    return await retriever(query.query, collection, hclient)


@app.get("/translate")
async def translate(query: TranslateQuery):
    return await translator(query.text, query.src, query.dest)


@app.get("/tts")
async def tts(query: TTSQuery):
    return await speaker(query.text, query.src)


async def gradio_interface(input_text, grade, subject, chapter, history):
    response = await agent(ChatQuery(query=input_text, grade=grade, subject=subject, chapter=chapter))

    if "text" in response:
        output = response["text"]
        history.append((input_text, output))

    elif "audios" in response:
        audio_data = base64.b64decode(response["audios"][0])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audiofile:
            audiofile.write(audio_data)
            audiofile.flush()

        return "", history, audiofile.name

    else:
        output = "Unexpected response format"
        history.append((input_text, output))

    return "", history, None


with gr.Blocks() as iface:
    gr.Markdown("# Agentic RAG Chatbot")
    gr.Markdown("Ask a question and get an answer from the chatbot. The response may be text or audio.")

    with gr.Row():
        grade = gr.Dropdown(choices=["1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12"], label="Grade", value="9", interactive=True)
        subject = gr.Dropdown(choices=["Math", "Science", "History"], label="Subject", value="Science", interactive=True)
        chapter = gr.Dropdown(choices=["1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12", "13", "14", "15", "16"], label="Chapter", value="11", interactive=True)

    chatbot = gr.Chatbot(label="Chat History")
    msg = gr.Textbox(label="Your message", placeholder="Type your message here...")

    state = gr.State([])
    audio_output = gr.Audio(label="Audio Response", type="filepath")  # Separate audio output component

    msg.submit(gradio_interface, inputs=[msg, grade, subject, chapter, state], outputs=[msg, chatbot, audio_output])

app = gr.mount_gradio_app(app, iface, path="/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
