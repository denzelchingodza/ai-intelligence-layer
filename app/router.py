from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.connectors.sentinel import query_sentinel
from app.connectors.stackscope import query_stackscope
from app.connectors.docuzen import query_docuzen

client = OpenAI(api_key=OPENAI_API_KEY)
def classify(question: str) -> str:
    """
    Asks GPT to classify the query into one of three tools.
    Returns: 'sentinel', 'stackscope', or 'docuzen'
    """
    response = client.chat.completions.create(
            model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a router. Classify the user's question into exactly one of these three categories:\n\n"
                    "sentinel   — questions about service uptime, monitors, incidents, whether something is down\n"
                    "stackscope — questions about developer skills, job market, salaries, trends, career advice\n"
                    "docuzen    — questions about a document, its contents, specific sections, or anything that requires reading a file\n\n"
                    "Reply with only the single word: sentinel, stackscope, or docuzen. Nothing else."
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

    if tool == "sentinel":
        return query_sentinel(question)
    elif tool == "stackscope":
        return query_stackscope(question)
    elif tool == "docuzen":
        return query_docuzen(question)
    else:
        # Fallback if GPT returns something unexpected
        return {
            "source": "unknown",
            "answer": "Could not determine which tool to use. Try rephrasing your question.",
            "metadata": {"raw_classification": tool},
        }