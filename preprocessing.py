from collections import defaultdict

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
                        "text": text.strip(),
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


def embed_pdf(path):
    doc = pymupdf.open(path)
    chunks = get_chunks(doc)
    return chunks
