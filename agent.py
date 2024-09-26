import os

from dotenv import load_dotenv
from strictjson import strict_json_async

from sarvam import speaker, translator

load_dotenv()

RAG_SYS_PROMPT = None
RAG_USER_PROMPT = None

AGENT_PROMPT = """You are an AI agent. 
  You are given three functions - retriever (Retreives information from a database), translator and a speaker (converts text to speech). 
  The database is a Grade {} {} Textbook. Your task is to assess the user query and determine which function to call. 
  If the function is to be called, return response as None. If any function is not needed, you can answer to the query yourself. Also identify keywords in the query,
  """


async def llm(system_prompt: str, user_prompt: str) -> str:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.get_env("GROQ_API_KEY"))

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


async def call_agent(user_prompt, grade, subject):
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
            "source": "Identify the sentence that the user wants to translate or speak. Retu 'none', type: Optional[str]",
            "response": "Your response, type: Optional[str]",
        },
        llm=llm,
    )
    return result


async def function_caller(user_prompt, grade, subject, client):
    result = call_agent(user_prompt, grade, subject)
    function = result["function"].lower()

    if function == "none":
        return result["response"]

    elif function == "retriever":
        collection = f"{grade}_{subject}"

        data = client.search(collection, user_prompt)
        data = [i.document for i in data]

        system_prompt = RAG_SYS_PROMPT.format(grade, subject)
        user_prompt = RAG_USER_PROMPT.format(user_prompt)

        response = await llm(system_prompt, user_prompt)

        return response

    elif function == "translator":
        return await translator(result["response"], result["src_lang"], result["dest_lang"])

    elif function == "speaker":
        return await speaker(result["response"], result["dest_lang"])
