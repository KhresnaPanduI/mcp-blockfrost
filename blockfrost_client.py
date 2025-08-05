import asyncio
import json
import os
from fastmcp import Client
import anthropic

async def main():
    mcp_server_url = "http://127.0.0.1:8000/mcp/"
    
    user_prompt = "Get the latest 5 transactions for the address addr1q8f06vecxlz2x0pag3j4x9q0hkqzpu83qpx5v7e2ra225tqadghk7rq4akmf6zatdcukakuxuykk80a3nkzz70svhmgq70c9xv"
    #user_prompt = "What are the totals for address addr1q8f06vecxlz2x0pag3j4x9q0hkqzpu83qpx5v7e2ra225tqadghk7rq4akmf6zatdcukakuxuykk80a3nkzz70svhmgq70c9xv"
    print(f"User Prompt: \"{user_prompt}\"")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set. Please export your key.")

    try:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    except Exception as e:
        print(f"Error initializing Anthropic client: {e}")
        return

    mcp_client = Client(mcp_server_url)

    async with mcp_client:
        tools = await mcp_client.list_tools()

        # *** THIS IS THE FIX ***
        # The tool definitions must be formatted in a specific way for the Anthropic API,
        # with an explicit 'input_schema' key.
        tool_definitions = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.model_json_schema()}
            for tool in tools
        ]

        print("\nAvailable tools:", [tool['name'] for tool in tool_definitions])

        print("\nSending prompt to Claude...")
        message = anthropic_client.messages.create(
            model="claude-4-sonnet-20250514",
            max_tokens=2048,
            tools=tool_definitions,
            messages=[{"role": "user", "content": user_prompt}],
        )

        if message.stop_reason == "tool_use":
            tool_use = next((block for block in message.content if block.type == 'tool_use'), None)
            if tool_use:
                tool_name = tool_use.name
                tool_input = tool_use.input
                
                print(f"\nClaude wants to use tool '{tool_name}' with input: {tool_input}")

                tool_result = await mcp_client.call_tool(tool_name, tool_input)

                print("\n--- API Result ---")
                #python_data = [item.model_dump() for item in tool_result.data]
                pretty_json = json.dumps(tool_result.structured_content, indent=2)
                print(pretty_json)
                print("--------------------")

                tool_response_for_llm = json.dumps(tool_result.structured_content)
                system_prompt = """
                You are helpful assistance that will be answering user question about Cardano blockchain. 
                For your context 1 ADA = 1,000,000 (1 million) Lovelace.
                Think and answer step by step before answering user questions, especially if it contain calculating big numbers.
                write out all your calculations
		"""
                final_response_message = anthropic_client.messages.create(
                    model="claude-4-sonnet-20250514",
                    max_tokens=2048,
                    tools=tool_definitions,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": message.content},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use.id,
                                    "content": tool_response_for_llm,
                                }
                            ],
                        },
                    ],
                )
                final_text = next((block.text for block in final_response_message.content if hasattr(block, 'text')), "Done.")
                print("\nFinal response from Claude:", final_text)

        else:
            print("\nClaude did not request to use a tool. Final response:", message.content)


if __name__ == "__main__":
    asyncio.run(main())
