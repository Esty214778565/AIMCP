import asyncio
import json
import os
import re
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

import httpx
from client import MCPClient
from dotenv import load_dotenv
from netfree_unstrict_ssl import unstrict_ssl

unstrict_ssl()
load_dotenv(Path(__file__).parent / ".env")


try:
    from google import genai
    from google.genai import types
except ImportError as exc:
    raise RuntimeError(
        "google-genai is not installed. Run: pip install google-genai"
    ) from exc


class ChatHost:
    def __init__(self):
        self.mcp_clients: list[MCPClient] = [
            MCPClient("./weather_USA.py"),
            MCPClient("./weather_Israel.py"),
        ]
        self.tool_clients: dict[str, tuple[MCPClient, str]] = {}
        self.clients_connected = False
        self.exit_stack = AsyncExitStack()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "No Gemini auth found. Set GEMINI_API_KEY in mcp/weather-chat_mcp/.env"
            )

        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.gemini = genai.Client(api_key=api_key)

    def _render_tool_prompt(self, available_tools: list[dict[str, Any]]) -> str:
        tool_lines = "\n".join(
            f"- {tool['name']}: {tool['description']}"
            for tool in available_tools
        )
        return (
            "You are a weather assistant for USA and Israel weather. "
            "When you need external information, use one of the available tools. "
            "If you want to call a tool, respond only with valid JSON exactly in this format:\n"
            "{\"tool\": \"tool_name\", \"input\": {...}}\n"
            "Do not include any extra text when requesting a tool. "
            "If you already have the answer, return the answer directly as plain text.\n\n"
            "Available tools:\n"
            f"{tool_lines}\n"
        )

    def _build_conversation(self, messages: list[dict[str, str]]) -> str:
        return "\n".join(
            f"{message['role'].upper()}: {message['content']}" for message in messages
        )

    async def _generate_text(self, prompt: str) -> str:
        response = await asyncio.to_thread(
            self.gemini.models.generate_content,
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                temperature=0.0,
                max_output_tokens=1000,
            ),
            contents=prompt,
        )
        return getattr(response, "text", str(response))

    def _parse_tool_request(self, text: str) -> dict[str, Any] | None:
        if not text:
            return None

        candidate = text.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                parsed = None
        else:
            match = re.search(r"(\{.*\})", candidate, flags=re.DOTALL)
            parsed = None
            if match:
                try:
                    parsed = json.loads(match.group(1))
                except json.JSONDecodeError:
                    parsed = None

        if not parsed or "tool" not in parsed or "input" not in parsed:
            return None

        return parsed

    async def connect_mcp_clients(self):
        """Connect all configured MCP clients once."""
        if self.clients_connected:
            return

        for client in self.mcp_clients:
            if client.session is None:
                await client.connect_to_server()

        if not self.mcp_clients:
            raise RuntimeError("No MCP clients are connected")

        self.clients_connected = True

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Collect tools from all MCP clients and map them back to their owner."""
        await self.connect_mcp_clients()
        self.tool_clients = {}
        available_tools: list[dict[str, Any]] = []

        for client in self.mcp_clients:
            if client.session is None:
                print(f"Warning: MCP client {client.client_name} is not connected, skipping")
                continue

            try:
                response = await client.session.list_tools()
                for tool in response.tools:
                    exposed_name = f"{client.client_name}__{tool.name}"
                    if exposed_name in self.tool_clients:
                        raise RuntimeError(f"Duplicate tool name detected: {exposed_name}")

                    self.tool_clients[exposed_name] = (client, tool.name)
                    available_tools.append(
                        {
                            "name": exposed_name,
                            "description": f"[{client.client_name}] {tool.description}",
                            "input_schema": tool.inputSchema,
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to get tools from {client.client_name}: {str(e)}")
                continue

        if not available_tools:
            raise RuntimeError("No tools available from any MCP client")

        return available_tools


    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        available_tools = await self.get_available_tools()
        tool_prompt = self._render_tool_prompt(available_tools)
        messages = [{"role": "user", "content": query}]

        while True:
            prompt = tool_prompt + "\nConversation:\n" + self._build_conversation(messages)
            text = await self._generate_text(prompt)
            tool_request = self._parse_tool_request(text)

            if not tool_request:
                return text.strip()

            tool_name = tool_request["tool"]
            tool_args = tool_request["input"]

            if tool_name not in self.tool_clients:
                raise RuntimeError(f"Unknown tool requested by model: {tool_name}")

            client, original_tool_name = self.tool_clients[tool_name]
            if client.session is None:
                raise RuntimeError(f"MCP client {client.client_name} is not connected")

            result = await client.session.call_tool(original_tool_name, tool_args)
            tool_output = str(result.content)

            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "tool_result", "content": tool_output})

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nchat_loop Error: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        for client in reversed(self.mcp_clients):
            await client.cleanup()
        await self.exit_stack.aclose()


async def main():
    host = ChatHost()
    try:
        await host.chat_loop()
    finally:
        await host.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print("\n" + response)
                
            except Exception as e:
                print(f"\nchat_loop Error: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        for client in reversed(self.mcp_clients):
            await client.cleanup()
        await self.exit_stack.aclose()


async def main():
    host = ChatHost()
    try:
        await host.chat_loop()
    finally:
        await host.cleanup()


if __name__ == "__main__":
    asyncio.run(main())