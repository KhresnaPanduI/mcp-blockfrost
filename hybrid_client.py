import asyncio
import json
import os
from fastmcp import Client
import anthropic

def extract_price_from_response(response_data: dict, symbol: str, convert: str) -> str:
    """A helper function to safely extract the price from the nested CMC response."""
    try:
        quote_object = response_data['data'][symbol.upper()][0]['quote'][convert.upper()]
        price = quote_object['price']
        return f"{price:,.4f}"
    except (KeyError, TypeError, IndexError):
        return "not found"

async def main():
    mcp_server_url = "http://127.0.0.1:8000/mcp/"

    # --- CHOOSE A PROMPT TO TEST ---
    user_prompt = "What's the current price of Cardano in USD?"
    #user_prompt = "Get the latest 5 transactions for the address addr1q8f06vecxlz2x0pag3j4x9q0hkqzpu83qpx5v7e2ra225tqadghk7rq4akmf6zatdcukakuxuykk80a3nkzz70svhmgq70c9xv"
    
    print(f"User Prompt: \"{user_prompt}\"")

    try:
        anthropic_client = anthropic.Anthropic()
    except Exception as e:
        print(f"Error initializing Anthropic client: {e}")
        return

    mcp_client = Client(mcp_server_url)

    async with mcp_client:
        tools = await mcp_client.list_tools()
        tool_definitions = [
            {"name": tool.name, "description": tool.description, "input_schema": tool.model_json_schema()}
            for tool in tools
        ]

        print("\nAvailable tools:", [tool['name'] for tool in tool_definitions])
        print("\nSending prompt to Claude...")
        
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
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
                data_dict = tool_result.structured_content

                # --- THIS IS THE DYNAMIC FIX ---
                # Check which tool was used and format the response for the LLM accordingly.
                tool_response_for_llm = ""
                if tool_name == 'get_latest_crypto_quotes':
                    price = extract_price_from_response(
                        data_dict,
                        tool_input.get("symbol", ""),
                        tool_input.get("convert", "USD")
                    )
                    tool_response_for_llm = f"Tool executed successfully. The price of {tool_input.get('symbol')} is ${price} {tool_input.get('convert', 'USD')}."
                
                elif tool_name in ['get_address_transactions', 'get_address_info', 'get_address_totals', 'get_address_extended_info']:
                    # For Blockfrost tools, give the full JSON data back to the LLM.
                    # This gives it all the context it needs to answer the user's question.
                    tool_response_for_llm = json.dumps(data_dict)
                
                else:
                    # A generic fallback for any other tools
                    tool_response_for_llm = f"Tool '{tool_name}' executed successfully."

                print("\n--- API Result ---")
                print(json.dumps(data_dict, indent=2))
                print("--------------------")

                print("\nSending concise result back to Claude...")
                print(f"Context for LLM: {tool_response_for_llm}") # For debugging

                system_prompt = """
                You are a helpful assistant that will be answering user questions about Cardano blockchain. 
                For your context, 1 ADA = 1,000,000 (1 million) Lovelace.
                Think step-by-step before answering user questions, especially if they involve calculations.
                When presenting transaction data, format it clearly for the user.
                """

                final_response_message = anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    tools=tool_definitions,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": message.content},
                        {
                            "role": "user",
                            "content": [
                                { "type": "tool_result", "tool_use_id": tool_use.id, "content": tool_response_for_llm }
                            ],
                        },
                    ],
                )
                
                final_text = next((block.text for block in final_response_message.content if hasattr(block, 'text')), "Done.")
                print("\n✅ Final response from Claude:", final_text)

        else:
            print("\nClaude did not request to use a tool. Final response:", message.content)


if __name__ == "__main__":
    asyncio.run(main())
