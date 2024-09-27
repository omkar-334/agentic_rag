import asyncio
import base64
import io
import json
from string import ascii_lowercase

import aiohttp

from client import HybridClient
from headers import random_headers
from preprocessing import index_pdf

grade_map = ascii_lowercase[:12]

subject_map = {
    "science": "esc1",
    "geography": "ess1",
    "economics": "ess2",
    "history": "ess3",
    "politics": "ess4",
}


def get_url(grade, subject, chapter):
    filename = grade_map[grade - 1] + subject_map[subject] + str(chapter).zfill(2)
    url = f"https://ncert.nic.in/textbook/pdf/{filename}.pdf"
    print(url)
    return url


async def get_book(grade, subject, chapters=None):
    book = {}
    if not chapters:
        chapters = range(1, 20)

    async with aiohttp.ClientSession() as session:
        print("Downloaded - ", end="")
        for i in chapters:
            url = get_url(grade, subject, i)

            pdf = await download(session, url)

            if pdf:
                collection = f"{grade}_{subject}_{i}"
                print(i, end="")
                book[collection] = pdf
            else:
                break
    print()
    return book


async def download(session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> io.BytesIO | None:
    for attempt in range(max_retries):
        try:
            headers = {"Accept": "application/pdf"} | random_headers()
            async with session.get(url, headers=headers, timeout=10) as r:
                r.raise_for_status()
                content = await r.read()
                return io.BytesIO(content)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** (attempt + 1))
            else:
                print(f"Max retries reached. Unable to download PDF from {url}")
        return None


async def upload_book(grade, subject, chapters=None):
    hclient = HybridClient()

    book = await get_book(grade, subject)
    print(type(book))
    for collection, pdf in book.items():
        print(collection)
        chunks = index_pdf(pdf, buffer=True)

        hclient.create(collection)
        hclient.insert(collection, chunks)


async def save_book_to_json(grade, subject, chapters=None):
    book = await get_book(grade, subject, chapters)
    result = {}

    for collection, pdf in book.items():
        chunks = index_pdf(pdf, buffer=True)

        serializable_chunks = []
        for chunk in chunks:
            serializable_chunk = {}
            for key, value in chunk.items():
                if isinstance(value, bytes):
                    serializable_chunk[key] = base64.b64encode(value).decode("utf-8")
                else:
                    serializable_chunk[key] = value
            serializable_chunks.append(serializable_chunk)

        result[collection] = serializable_chunks

    with open(f"{grade}_{subject}.json", "w") as f:
        json.dump(result, f)


def upload_book_from_json(json_file_path):
    hclient = HybridClient()

    with open(json_file_path, "r") as f:
        data = json.load(f)

    for collection, serialized_chunks in data.items():
        chunks = []
        for serialized_chunk in serialized_chunks:
            chunk = {}
            for key, value in serialized_chunk.items():
                if isinstance(value, str) and value.startswith("b'") and value.endswith("'"):
                    chunk[key] = base64.b64decode(value[2:-1])
                else:
                    chunk[key] = value
            chunks.append(chunk)

        hclient.create(collection)
        hclient.insert(collection, chunks)
