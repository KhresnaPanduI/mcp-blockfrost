import os
import httpx
import yaml
from pathlib import Path
from fastmcp import FastMCP

# 1. Load the Blockfrost Project ID from environment variables for security
project_id = os.getenv("BLOCKFROST_PROJECT_ID")
if not project_id:
    raise ValueError("BLOCKFROST_PROJECT_ID environment variable not set.")

# 2. Define the API base URL and configure the HTTP client with the auth header
API_BASE_URL = "https://cardano-mainnet.blockfrost.io/api/v0"
headers = {"project_id": project_id}
client = httpx.AsyncClient(base_url=API_BASE_URL, headers=headers)

# 3. Load the OpenAPI specification from the YAML file
spec_path = Path(__file__).parent / "blockfrost_openapi.yaml"
with open(spec_path, "r") as f:
    openapi_spec = yaml.safe_load(f)

# 4. Create the MCP server from the OpenAPI specification
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    name="BlockfrostMCP"
)

if __name__ == "__main__":
    print("Starting Blockfrost MCP Server...")
    print(f"Loaded {len(mcp._tool_manager._tools)} tools from the OpenAPI spec.")
    mcp.run(transport="http", port=8000)
