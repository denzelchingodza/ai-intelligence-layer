from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.connectors.stackscope import query_stackscope
from app.connectors.docuzen import query_docuzen

client = OpenAI(api_key=OPENAI_API_KEY)


def classify(question: str) -> str:
    """
    Asks GPT to classify the query into one of two tools.
    Returns: 'stackscope' or 'docuzen'
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a router. Classify the user's question into exactly one of these two categories:\n\n"
                    "stackscope — questions about developer skills, job market, salaries, trends, career advice\n"
                    "docuzen    — questions about a document, its contents, specific sections, or anything that requires reading a file\n\n"
                    "Reply with only the single word: stackscope or docuzen. Nothing else."
                ),
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content.strip().lower()


def route(question: str) -> dict:
    """
    Classifies the question and calls the right connector.
    """
    tool = classify(question)

    if tool == "stackscope":
        return query_stackscope(question)
    elif tool == "docuzen":
        return query_docuzen(question)
    else:
        return {
            "source": "unknown",
            "answer": "Could not determine which tool to use. Try rephrasing your question.",
            "metadata": {"raw_classification": tool},
        }
