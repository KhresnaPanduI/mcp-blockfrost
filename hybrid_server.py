import os
import httpx
import yaml
import asyncio  # We still need asyncio to run our helper function
from pathlib import Path
from fastmcp import FastMCP

# --- All setup remains synchronous ---
main_mcp = FastMCP(name="HybridCryptoMCP")
print("Initialized Hybrid MCP Server...")

# --- 1. Configure and Mount Blockfrost Server ---
try:
    print("\nConfiguring Blockfrost API...")
    blockfrost_project_id = os.getenv("BLOCKFROST_PROJECT_ID")
    if not blockfrost_project_id:
        raise ValueError("BLOCKFROST_PROJECT_ID environment variable not set.")

    blockfrost_client = httpx.AsyncClient(
        base_url="https://cardano-mainnet.blockfrost.io/api/v0",
        headers={"project_id": blockfrost_project_id}
    )
    blockfrost_spec_path = Path(__file__).parent / "blockfrost_openapi.yaml"
    with open(blockfrost_spec_path, "r") as f:
        blockfrost_spec = yaml.safe_load(f)

    blockfrost_sub_server = FastMCP.from_openapi(
        openapi_spec=blockfrost_spec, client=blockfrost_client
    )
    main_mcp.mount(blockfrost_sub_server)
    print(f"✅ Mounted Blockfrost tools.")
except Exception as e:
    print(f"❌ Failed to configure Blockfrost: {e}")

# --- 2. Configure and Mount CoinMarketCap Server ---
try:
    print("\nConfiguring CoinMarketCap API...")
    cmc_api_key = os.getenv("COINMARKETCAP_API_KEY")
    if not cmc_api_key:
        raise ValueError("COINMARKETCAP_API_KEY environment variable not set.")

    cmc_client = httpx.AsyncClient(
        base_url="https://pro-api.coinmarketcap.com",
        headers={"X-CMC_PRO_API_KEY": cmc_api_key}
    )
    cmc_spec_path = Path(__file__).parent / "coinmarketcap_openapi.yaml"
    with open(cmc_spec_path, "r") as f:
        cmc_spec = yaml.safe_load(f)
    
    cmc_sub_server = FastMCP.from_openapi(
        openapi_spec=cmc_spec,
        client=cmc_client
    )
    main_mcp.mount(cmc_sub_server)
    print(f"✅ Mounted CoinMarketCap tools.")
except Exception as e:
    print(f"❌ Failed to configure CoinMarketCap: {e}")

# --- 3. Run the Server ---
if __name__ == "__main__":
    # Define a small async helper function just to get the tool count
    async def get_total_tools(mcp_instance):
        # We 'await' the async method here, inside an async function
        all_tools = await mcp_instance._tool_manager.get_tools()
        return len(all_tools)

    # Use asyncio.run() to execute our helper and get the count
    total_tools = asyncio.run(get_total_tools(main_mcp))
    
    print(f"\n🚀 Starting Hybrid MCP Server with a total of {total_tools} tools.")
    
    # Now that we have the count, call the normal, synchronous run() method
    try:
        main_mcp.run(transport="http", port=8000)
    except KeyboardInterrupt:
        print("\nServer shut down.")
