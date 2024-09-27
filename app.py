import base64
import io

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import function_caller

app = FastAPI()

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


@app.post("/chat")
async def chat(query: ChatQuery):
    result = await function_caller(query.query, query.grade, query.subject, query.chapter)

    if isinstance(result, str):
        return {"text": result}
    elif isinstance(result, bytes) or (isinstance(result, str) and result.startswith("data:audio")):
        if isinstance(result, bytes):
            audio_b64 = base64.b64encode(result).decode()
        else:
            audio_b64 = result.split(",")[1]  # Remove the "data:audio/wav;base64," prefix
        return {"audio": audio_b64}
    else:
        return {"error": "Unexpected result type"}


async def gradio_interface(input_text, grade, subject, chapter):
    response = await chat(ChatQuery(query=input_text, grade=grade, subject=subject, chapter=chapter))
    if "text" in response:
        return response["text"], None
    elif "audio" in response:
        audio_data = base64.b64decode(response["audio"])
        return "Audio response generated", (44100, io.BytesIO(audio_data))
    else:
        return "Unexpected response format", None


iface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter your question here..."),
        gr.Dropdown(choices=["1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12"], label="Grade", value="9", interactive=True),
        gr.Dropdown(choices=["Math", "Science", "History"], label="Subject", value="Science", interactive=True),
        gr.Dropdown(choices=["1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12", "13", "14", "15", "16"], label="Chapter", value="11", interactive=True),
    ],
    outputs=[gr.Textbox(label="Response"), gr.Audio(label="Audio Response")],
    title="Agentic RAG Chatbot",
    description="Ask a question and get an answer from the chatbot. The response may be text or audio.",
)

app = gr.mount_gradio_app(app, iface, path="/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
