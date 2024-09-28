from dotenv import load_dotenv
from strictjson import strict_json_async

from prompts import AGENT_PROMPT, RAG_SYS_PROMPT, RAG_USER_PROMPT
from sarvam import speaker, translator

load_dotenv()


async def llm(system_prompt: str, user_prompt: str) -> str:
    import os

    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    chat_completion = await client.chat.completions.create(
        messages=messages,
        model="llama3-70b-8192",
        temperature=0.3,
        max_tokens=360,
        top_p=1,
        stop=None,
        stream=False,
    )

    return chat_completion.choices[0].message.content


async def call_agent(user_prompt, collection):
    grade, subject, chapter = collection.split("_")

    system_prompt = AGENT_PROMPT.format(grade, subject)

    result = await strict_json_async(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_format={
            "function": 'Type of function to call, type: Enum["retriever", "translator", "speaker", "none"]',
            "keywords": "Array of keywords, type: List[str]",
            "src_lang": "Identify the language that the user query is in, type: str",
            "dest_lang": """Identify the target language from the user query if the function is either "translator" or "speaker". If language is not found, return "none", 
                                    type: Enum["hindi", "bengali", "kannada", "malayalam", "marathi", "odia", "punjabi", "tamil", "telugu", "english", "gujarati", "none"]""",
            "source": "Identify the sentence that the user wants to translate or speak. Else return 'none', type: Optional[str]",
            "response": "Your response, type: Optional[str]",
        },
        llm=llm,
    )
    return result


async def retriever(user_prompt, collection, client):
    grade, subject, chapter = collection.split("_")

    data = client.search(collection, user_prompt)
    data = [i.document for i in data]

    system_prompt = RAG_SYS_PROMPT.format(subject, grade)
    user_prompt = RAG_USER_PROMPT.format(data, user_prompt)

    return await llm(system_prompt, user_prompt)


async def function_caller(user_prompt, collection, client):
    result = await call_agent(user_prompt, collection)
    function = result["function"].lower()

    if function == "none":
        return {"text": result["response"]}

    elif function == "retriever":
        response = await retriever(user_prompt, collection, client)
        return {"text": response}

    elif function == "translator":
        return await translator(result["source"], result["src_lang"], result["dest_lang"])

    elif function == "speaker":
        return await speaker(result["source"])
