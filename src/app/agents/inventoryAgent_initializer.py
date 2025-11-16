"""Inventory Agent Initializer - Creates or updates the Zava Inventory Agent"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool,FunctionTool, ToolSet
from typing import Callable, Set, Any
import json
from tools.inventoryCheck import inventory_check
from dotenv import load_dotenv

# Load environment variables from .env file in src directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=env_path)

IA_PROMPT_TARGET = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'prompts', 'InventoryAgentPrompt.txt')
with open(IA_PROMPT_TARGET, 'r', encoding='utf-8') as file:
    IA_PROMPT = file.read()

project_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
if not project_endpoint:
    raise ValueError("AZURE_AI_AGENT_ENDPOINT environment variable is required but not set")

agent_id = os.getenv("inventory_agent")  # Use getenv instead of environ to avoid KeyError


project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
)

user_functions: Set[Callable[..., Any]] = {
    inventory_check,
}

# Initialize agent toolset with user functions
functions = FunctionTool(user_functions)
toolset = ToolSet()
toolset.add(functions)
project_client.agents.enable_auto_function_calls(tools=functions)

with project_client:
    agent_exists = False
    if agent_id:
        try:
            # Check if agent exists.
            agent = project_client.agents.get_agent(agent_id)
            print(f"Retrieved existing agent, ID: {agent.id}")
            agent_exists = True
        except Exception as e:
            print(f"Agent not found or error retrieving: {e}")
            agent_exists = False
    
    if agent_exists:
        agent = project_client.agents.update_agent(
            agent_id=agent.id,
            model=os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"],  # Model deployment name
            name="Zava Inventory Agent",  # Name of the agent
            instructions=IA_PROMPT,  # Updated instructions for the agent
            # toolset=toolset
        )
        print(f"Updated agent, ID: {agent.id}")
    else:
        agent = project_client.agents.create_agent(
            model=os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"],  # Model deployment name
            name="Zava Inventory Agent",  # Name of the agent
            instructions=IA_PROMPT,  # Instructions for the agent
            # toolset=toolset
        )
        print(f"Created agent, ID: {agent.id}")
