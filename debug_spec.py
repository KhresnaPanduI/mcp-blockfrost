import httpx
import yaml
import asyncio
from pathlib import Path
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

print("--- Starting OpenAPI Specification Debugger ---")

spec_file_to_test = "coinmarketcap_openapi.yaml"
spec_path = Path(__file__).parent / spec_file_to_test

print(f"Attempting to load and parse '{spec_path}'...")

try:
    with open(spec_path, "r") as f:
        openapi_spec = yaml.safe_load(f)
    print("✅ YAML file loaded successfully.")

    dummy_client = httpx.AsyncClient(base_url="https://example.com")

    # The from_openapi factory returns a special subclass.
    # We create a main server and mount the sub-server onto it to test properly.
    main_server = FastMCP()
    sub_server = FastMCP.from_openapi(openapi_spec=openapi_spec, client=dummy_client)
    main_server.mount(sub_server)
    
    print("✅ FastMCP parsed and mounted the specification successfully!")

    # To get the tools, we now need an async context
    async def get_tool_count():
        # The tools are managed internally, so we access them via this async method
        tools = await main_server._tool_manager.get_tools()
        print(f"✅ Found {len(tools)} tool(s): {[tool.name for tool in tools]}")

    asyncio.run(get_tool_count())
    
    print("\n--- ✅ CONCLUSION: Your coinmarketcap_openapi.yaml file is CORRECT. ---")
    print("Please now STOP your hybrid_server.py with Ctrl+C and RESTART it.")

except ToolError as e:
    if "PointerToNowhere" in str(e):
        print(f"\n--- ❌ ERROR: The YAML file is INVALID. ---")
        print(f"Error Details: {e}")
    else:
        print(f"\n--- ❌ An unexpected ToolError occurred: {e} ---")
except Exception as e:
    print(f"\n--- ❌ An unexpected generic error occurred: {e} ---")
