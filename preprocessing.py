import re
from collections import OrderedDict, defaultdict

import pymupdf


def sort_text(chunks):
    x_threshold = 300
    left_column = []
    right_column = []

    for chunk in chunks:
        if chunk["x"] < x_threshold:
            left_column.append(chunk)
        else:
            right_column.append(chunk)

    # Sort the chunks within each column based on the y-coordinate
    left_column = sorted(left_column, key=lambda item: item["y"])
    right_column = sorted(right_column, key=lambda item: item["y"])

    sorted_text = left_column + right_column
    return sorted_text


def majority_element(spans, param):
    char_count = defaultdict(int)

    for span in spans:
        span_text = span["text"]
        span_param = span[param]  # Get the color or size for this span
        char_count[span_param] += len(span_text)  # Count characters

    # Return the parameter value with the highest character count
    return max(char_count, key=char_count.get, default=None)


def clean_text(text):
    """Cleans repeated text (OCR error)"""
    words = text.split()
    unique_words = OrderedDict.fromkeys(words)
    cleaned_text = " ".join(unique_words)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    return cleaned_text


def get_chunks(doc):
    allchunks = []

    # Page Iteration
    for page_num in range(doc.page_count):
        chunks = []
        page = doc[page_num]

        # Filter images (not needed)
        blocks = [i for i in page.get_text("dict")["blocks"] if "image" not in i]

        # Block Iteration
        for block in blocks:
            text = ""
            spans = []

            # Line iteration
            for line in block["lines"]:
                for span in line["spans"]:
                    # Only include text with a size greater than 9
                    if span["size"] > 9:
                        span_text = span["text"]
                        text += span_text + " "
                        spans.append(span)  # Store the span for majority calculation

            # Filter empty strings
            if text.strip():
                chunks.append(
                    {
                        "text": clean_text(text.strip()),
                        "page": page_num,
                        "x": block["bbox"][0],
                        "y": block["bbox"][1],
                        "color": majority_element(spans, "color"),
                        "size": majority_element(spans, "size"),
                    }
                )

        # Sort text according to column order
        allchunks.extend(sort_text(chunks))
    return allchunks


def process_activities(chunks):
    """Groups lines of 'Activity' together"""
    # activities = []
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        if "Activity" in chunk["text"]:
            activity = chunk.copy()
            activity_size = chunks[i + 1]["size"] if i + 1 < len(chunks) else None

            j = i + 1
            while j < len(chunks) and chunks[j]["size"] == activity_size:
                activity["text"] += "\n" + chunks[j]["text"]
                j += 1

            # Replace the range of chunks with the single activity chunk
            chunks[i:j] = [activity]

            # activities.append(activity)
            i += 1
        else:
            i += 1

    return chunks


def index_pdf(path, buffer=False):
    if buffer:
        doc = pymupdf.open(stream=path, filetype="pdf")
    else:
        doc = pymupdf.open(path)
    chunks = get_chunks(doc)
    chunks = process_activities(chunks)
    print("--- pdf indexed")
    return chunks
