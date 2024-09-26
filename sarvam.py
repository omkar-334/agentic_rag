import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

code_map = {
    "hindi": "hi-IN",
    "bengali": "bn-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "marathi": "mr-IN",
    "odia": "od-IN",
    "punjabi": "pa-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "english": "en-IN",
    "gujarati": "gu-IN",
}


async def translator(text, src, dest):
    async with aiohttp.ClientSession() as session:
        url = "https://api.sarvam.ai/translate"

        payload = {
            "input": text,
            "source_language_code": code_map[src],
            "target_language_code": code_map[dest],
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True,
        }
        headers = {"Content-Type": "application/json", "api-subscription-key": os.getenv("SARVAM_API_KEY")}
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                output = await response.text()
                return output


async def speaker(text, dest):
    async with aiohttp.ClientSession() as session:
        url = "https://api.sarvam.ai/text-to-speech"

        payload = {
            "inputs": [text],
            "target_language_code": code_map[dest],
            "speaker": "meera",
            "pitch": 0,
            "pace": 1.65,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v1",
        }
        headers = {"Content-Type": "application/json", "api-subscription-key": os.getenv("SARVAM_API_KEY")}
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                output = await response.read()
                return output
