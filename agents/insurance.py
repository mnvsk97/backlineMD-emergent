from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

insurance_agent = create_deep_agent(
        name="insurance_agent",
        model=model,
        system_prompt="You are an agent that can help with verifying insurance coverage of patients for fertility treatments",
        tools=[],
    )
