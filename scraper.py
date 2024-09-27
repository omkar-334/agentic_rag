import io
from string import ascii_lowercase

import aiohttp

from client import HybridClient
from preprocessing import index_pdf

grade_map = ascii_lowercase[:10]

subject_map = {
    "science": "esc1",
    "geography": "ess1",
    "economics": "ess2",
    "history": "ess3",
    "politics": "ess4",
}


def get_url(grade, subject, chapter):
    filename = grade_map[grade] + subject_map[subject] + str(chapter).zfill(2)
    url = f"https://ncert.nic.in/textbook/pdf/{filename}.pdf"
    return url


async def get_book(grade, subject):
    book = {}
    chapter_num = 1
    async with aiohttp.ClientSession() as session:
        while True:
            url = get_url(grade, subject, chapter_num)

            pdf = download(session, url)

            if pdf:
                collection = f"{grade}_{subject}"
                book[collection] = pdf
            else:
                break
    return book


async def download(session, url):
    try:
        async with session.get(url, timeout=10) as r:
            r.raise_for_status()

            pdf_content = io.BytesIO()
            async for chunk in r.content.iter_chunked(1000000):
                pdf_content.write(chunk)

            pdf_content.seek(0)
            return pdf_content

    except Exception as e:
        print(f"Error downloading or processing PDF: {e}")
        return None


def upload_book(grade, subject):
    hclient = HybridClient()

    book = get_book(grade, subject)
    for collection, pdf in book.items():
        chunks = index_pdf(pdf)

        hclient.create(collection)
        hclient.insert(collection, chunks)
