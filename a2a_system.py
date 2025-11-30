import os
import json
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

load_dotenv()

class AgentCard(BaseModel):
    name: str
    description: str
    capabilities: List[str]

class ManagerAgent:
    def __init__(self):
        endpoint = "https://models.github.ai/inference"
        token = os.environ["OPENAI_API_KEY"]
        self.client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(token),
        )
        self.model_name = "gpt-4o-mini"

        self.known_agents = {
            "devops_runner": AgentCard(
                name="DevOps_Runner",
                description="Can list, trigger, and CREATE GitHub CI/CD workflows.",
                capabilities=["list_workflows", "create_basic_pipeline"]
            )
        }

    def run_mission(self, user_objective: str):
        print(f"[Manager]: Objective received -> '{user_objective}'")
        
        agent_info = self.known_agents["devops_runner"].model_dump_json()
        
        prompt = f"""You are an Orchestrator. 
User Goal: "{user_objective}"

Available Agent: {agent_info}

Rules:
1. If the user wants to check/list pipelines, use 'list_workflows'.
2. If the user wants to CREATE a pipeline, or if the goal implies creating one because none exist, use 'create_basic_pipeline'.
3. Do NOT just list workflows if the goal is to create one.

Return a JSON object with:
- "agent_name": name of agent
- "tool": tool function name
- "args": dictionary of arguments

IMPORTANT: Return ONLY valid JSON, no other text."""
        
        response = self.client.complete(
            model=self.model_name,
            messages=[UserMessage(prompt)],
            temperature=1.0,
            top_p=1.0,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        print(f"[Manager]: Raw response: {content[:100]}...")
        
        try:
            plan = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[WARNING] JSON parsing failed: {e}")
            print(f"Full response: {content}")
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                raise ValueError(f"Could not parse JSON from response: {content}")
        
        print(f"[Manager]: Plan -> {plan['tool']}")
        
        return self._dispatch_a2a_message(plan)

    def _dispatch_a2a_message(self, plan):
        if plan['agent_name'] == "DevOps_Runner":
            worker = DevOpsAgent()
            result = worker.receive_task(plan['tool'], plan.get('args', {}))
            print(f"[Manager]: Outcome -> {result}")
            return result
        return None

class DevOpsAgent:
    def receive_task(self, tool_name: str, args: dict) -> str:
        import devops_server as tools
        
        if tool_name == "list_workflows":
            return tools.list_workflows()
        elif tool_name == "create_basic_pipeline":
            return tools.create_basic_pipeline()
        return "Error: Unknown tool."

if __name__ == "__main__":
    system = ManagerAgent()
    
    print("--- Step 1: Check ---")
    result = system.run_mission("Check if we have any pipelines.")
    
    print("\n--- Step 2: Create New Workflow ---")
    if result and "No workflows found" in result:
        print("No existing workflows - creating the first one...")
        system.run_mission("Create a new pipeline.")
    else:
        print("Workflows exist - creating an additional one...")
        system.run_mission("Create a new additional pipeline.")