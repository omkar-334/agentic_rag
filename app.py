import base64
import sys
from datetime import datetime
from io import StringIO

import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import function_caller, retriever
from client import HybridClient
from sarvam import save_audio, speaker, translator

app = FastAPI()
hclient = HybridClient()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DebugCapture(StringIO):
    def __init__(self):
        super().__init__()
        self.debug_history = []
        self.new_entry = True

    def write(self, s):
        if s.strip():
            if self.new_entry:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.debug_history.append(f"[{timestamp}] {s.strip()}")
                self.new_entry = False
            else:
                self.debug_history[-1] += f"\n{s.strip()}"
        else:
            self.new_entry = True

        if len(self.debug_history) > 10:  # Limit log history memory consumption
            self.debug_history.pop(0)

        return super().write(s)


debug_capture = DebugCapture()
sys.stdout = debug_capture


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


# API Endpoints
@app.get("/agent")
async def agent(query: ChatQuery):
    collection = f"{query.grade}_{query.subject.lower()}_{query.chapter}"
    return await function_caller(query.query, collection, hclient)


@app.get("/rag")
async def rag(query: ChatQuery):
    collection = f"{query.grade}_{query.subject.lower()}_{query.chapter}"
    return await retriever(query.query, collection, hclient)


@app.get("/translate")
async def translate(query: TranslateQuery):
    return await translator(query.text, query.src, query.dest)


@app.get("/tts")
async def tts(query: TTSQuery):
    return await speaker(query.text, query.src)


# Gradio interface
async def gradio_interface(input_text, grade, subject, chapter, history):
    response = await agent(ChatQuery(query=input_text, grade=grade, subject=subject, chapter=chapter))

    if "text" in response:
        output = response["text"]
        history.append((input_text, {"type": "text", "content": output}))
    elif "audios" in response:
        audio_data = base64.b64decode(response["audios"][0])
        audio_path = save_audio(audio_data)
        history.append((input_text, {"type": "audio", "content": audio_path}))
    else:
        output = "Unexpected response format"
        history.append((input_text, {"type": "text", "content": output}))
    return "", history


def format_history(history):
    formatted_history = []
    for human, assistant in history:
        formatted_history.append((human, None))
        if assistant["type"] == "text":
            formatted_history.append((None, assistant["content"]))
        elif assistant["type"] == "audio":
            formatted_history.append((None, gr.Audio(value=assistant["content"], visible=True)))

    if len(formatted_history) > 10:  # Limit history memory consumption
        formatted_history.pop(0)
    return formatted_history


# Debug functions
def update_debug_output():
    return "\n".join(debug_capture.debug_history)


def clear_debug_history():
    debug_capture.debug_history = []
    return "Debug history cleared."


def toggle_debug_modal(visible):
    return gr.update(visible=visible)


# Gradio UI setup
with gr.Blocks() as iface:
    gr.Markdown("# Agentic RAG Chatbot")

    # Main header row
    with gr.Row():
        with gr.Column(scale=19):
            gr.Markdown("Ask a question and get an answer from the chatbot. The response may be text or audio.")
        with gr.Column(scale=1, min_width=50):
            debug_button = gr.Button("🖥️", size="sm")

    # Chat input and interaction
    with gr.Row():
        with gr.Column(scale=20):
            with gr.Row():
                grade = gr.Dropdown(choices=["1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12"], label="Grade", value="9", interactive=True)
                subject = gr.Dropdown(choices=["Math", "Science", "History"], label="Subject", value="Science", interactive=True)
                chapter = gr.Dropdown(choices=["1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12", "13", "14", "15", "16"], label="Chapter", value="11", interactive=True)

            chatbot = gr.Chatbot(label="Chat History")
            msg = gr.Textbox(label="Your message", placeholder="Type your message here...")
            state = gr.State([])

    # Debugging modal
    with gr.Group(visible=False) as debug_modal:
        debug_output = gr.TextArea(label="Debug Terminal", interactive=False)
        with gr.Row():
            refresh_button = gr.Button("Refresh Debug History")
            clear_button = gr.Button("Clear Debug History")
            close_button = gr.Button("Close")

    # Submit action
    msg.submit(gradio_interface, inputs=[msg, grade, subject, chapter, state], outputs=[msg, state]).then(format_history, inputs=[state], outputs=[chatbot])

    # Debug button click
    debug_button.click(lambda: toggle_debug_modal(True), outputs=debug_modal).then(update_debug_output, inputs=[], outputs=[debug_output])

    # Debug modal buttons
    refresh_button.click(update_debug_output, inputs=[], outputs=[debug_output])
    clear_button.click(clear_debug_history, inputs=[], outputs=[debug_output])
    close_button.click(lambda: toggle_debug_modal(False), outputs=debug_modal)

app = gr.mount_gradio_app(app, iface, path="/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
