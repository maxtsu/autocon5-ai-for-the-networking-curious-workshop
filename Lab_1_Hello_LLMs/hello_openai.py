from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # reads .env, sets OPENAI_API_KEY in environment

print(os.environ)

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Explain OSPF in one sentence."}
    ],
)

print(response.choices[0].message.content)
print(f"\nTokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")