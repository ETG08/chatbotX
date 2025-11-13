"""
Azure AI Service - Using foundry_local (Emily's proven approach)
Handles conversation with local AI model and integrates with MCP.
"""

from typing import List, Dict, Any
import json
import re
import openai
from foundry_local import FoundryLocalManager


class AzureAIService:
    """
    Manages conversation with Azure AI Foundry Local model.
    Uses the same approach Emily has used before.
    """
    
    def __init__(self, model_alias="qwen2.5-7b"):
        """Initialize AI service with foundry_local."""
        print("🔄 Initializing Azure AI Foundry Local...")
        
        self.model_alias = model_alias
        self.manager = None
        self.client = None
        
        # Initialize the model
        self._initialize_model()
        
        self.system_prompt = """You are a helpful company assistant. You help employees with:
- Finding employee information
- Checking leave balances
- Getting department information
- Viewing company holidays
- Reading announcements
- Searching policies

IMPORTANT: You MUST use the provided tools to look up information. Do not make up information.

When you need to look up information, respond with EXACTLY this format:
TOOL_CALL: <tool_name> {"parameter": "value"}

Examples:
- User asks "Who is John Doe?" -> You respond: TOOL_CALL: search_employees {"search": "John Doe"}
- User asks "What holidays do we have?" -> You respond: TOOL_CALL: get_holidays {}
- User asks "Show leave balance for EMP001" -> You respond: TOOL_CALL: get_leave_balance {"employee_id": "EMP001"}
- User asks "Tell me about the engineering department" -> You respond: TOOL_CALL: get_departments {}

Always be helpful, professional, and concise."""
    
    def _initialize_model(self):
        """Initialize and start the foundry local model"""
        try:
            print(f"🔄 Initializing {self.model_alias}...")
            print("   (First time: downloads model)")
            
            # Initialize FoundryLocalManager
            self.manager = FoundryLocalManager(self.model_alias)
            
            # Create OpenAI client pointing to local endpoint
            self.client = openai.OpenAI(
                base_url=self.manager.endpoint,
                api_key=self.manager.api_key
            )
            
            print(f"✅ Model ready!")
            print(f"   Endpoint: {self.manager.endpoint}")
            
        except Exception as e:
            print(f"❌ Error initializing model: {e}")
            print("\nTroubleshooting:")
            print("1. Run: foundry model list")
            print("2. Run: foundry service ps")
            raise
    
    def format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """Format MCP tools as text for the model's context."""
        tools_text = "\n\n=== AVAILABLE TOOLS ===\n"
        
        for tool in tools:
            tools_text += f"\n**{tool['name']}**\n"
            tools_text += f"Description: {tool['description']}\n"
            
            properties = tool['input_schema'].get('properties', {})
            if properties:
                tools_text += "Parameters:\n"
                for param_name, param_info in properties.items():
                    required = param_name in tool['input_schema'].get('required', [])
                    req_text = "(required)" if required else "(optional)"
                    tools_text += f"  - {param_name} {req_text}: {param_info.get('description', '')}\n"
        
        tools_text += "\n=== HOW TO USE TOOLS ===\n"
        tools_text += "When a user asks for information, you MUST use a tool to look it up.\n"
        tools_text += "Respond with EXACTLY this format (copy it exactly!):\n"
        tools_text += 'TOOL_CALL: tool_name {"param1": "value1", "param2": "value2"}\n\n'
        
        tools_text += "EXAMPLES OF CORRECT TOOL USAGE:\n"
        tools_text += 'User: "Who is John Doe?" -> Your response: TOOL_CALL: search_employees {"search": "John Doe"}\n'
        tools_text += 'User: "What are our holidays?" -> Your response: TOOL_CALL: get_holidays {}\n'
        tools_text += 'User: "Show me leave for EMP001" -> Your response: TOOL_CALL: get_leave_balance {"employee_id": "EMP001"}\n'
        tools_text += 'User: "Find someone in engineering" -> Your response: TOOL_CALL: search_employees {"department": "engineering"}\n'
        tools_text += 'User: "What are the departments?" -> Your response: TOOL_CALL: get_departments {}\n'
        tools_text += 'User: "Show announcements" -> Your response: TOOL_CALL: get_announcements {}\n'
        tools_text += 'User: "What is the remote work policy?" -> Your response: TOOL_CALL: search_policies {"search": "remote work"}\n'
        tools_text += "\n======================\n"
        
        return tools_text
    
    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from model response.
        Pattern: TOOL_CALL: tool_name {"param": "value"}
        """
        tool_calls = []
        
        # Multiple pattern variations
        patterns = [
            r'TOOL_CALL:\s*(\w+)\s*(\{[^}]*\})',
            r'Tool:\s*(\w+)\s*(\{[^}]*\})',
            r'USE_TOOL:\s*(\w+)\s*(\{[^}]*\})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            
            for tool_name, args_json in matches:
                try:
                    args_json = args_json.strip()
                    arguments = json.loads(args_json)
                    
                    tool_calls.append({
                        "name": tool_name,
                        "arguments": arguments
                    })
                    
                    print(f"✅ Parsed tool call: {tool_name} with args {arguments}")
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse tool arguments: {args_json}")
                    print(f"   Error: {e}")
        
        return tool_calls
    
    def clean_response(self, response: str) -> str:
        """Remove tool call syntax from final response."""
        patterns = [
            r'TOOL_CALL:.*?\n',
            r'Tool:.*?\{[^}]*\}\n',
            r'USE_TOOL:.*?\n'
        ]
        
        cleaned = response
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[Dict[str, Any]]
    ) -> str:
        """
        Generate response from Azure AI Foundry Local model.
        Uses OpenAI-compatible API (same as your QA system).
        """
        
        if not self.client:
            raise RuntimeError("Model not initialized")
        
        # Build prompt with tools
        tools_description = self.format_tools_for_prompt(tools)
        
        # Format conversation
        formatted_messages = [
            {
                "role": "system",
                "content": self.system_prompt + "\n" + tools_description
            }
        ]
        
        # Add conversation history
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        print(f"\n{'='*60}")
        print(f"📤 Sending to model")
        print(f"📋 Last message: {messages[-1]['content'][:100]}...")
        
        try:
            # Get model ID
            model_id = self.manager.get_model_info(self.model_alias).id
            
            # Call local model API (OpenAI-compatible)
            response = self.client.chat.completions.create(
                model=model_id,
                messages=formatted_messages,
                temperature=0.3,  # Lower temperature for more consistent tool calling
                max_tokens=512
            )
            
            # Extract generated text
            generated_text = response.choices[0].message.content.strip()
            
            print(f"📥 Model response: {generated_text[:150]}...")
            print(f"{'='*60}\n")
            
            return generated_text
            
        except Exception as e:
            error_msg = f"Error generating response: {e}"
            print(f"❌ {error_msg}")
            return error_msg
