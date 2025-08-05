# Blockfrost Cardano API with FastMCP and an LLM

This project demonstrates how to create a powerful bridge between a Large Language Model (LLM) like Claude and the Cardano blockchain using the Blockfrost API. It uses `FastMCP` to instantly convert a set of Blockfrost REST endpoints into a secure, LLM-ready tool server.

An LLM can then leverage these tools to answer natural language questions about Cardano addresses, such as "What are the totals for this address?" or "Show me the last 5 transactions."

## Features

-   **MCP Server from OpenAPI:** The `FastMCP.from_openapi` method is used to automatically generate an MCP server from a simple `YAML` specification.
-   **LLM Agent Integration:** A client application demonstrates how to use the Anthropic Claude API to interpret a user's prompt, select the correct tool, and execute it.
-   **Secure Credential Management:** API keys (for Blockfrost and Anthropic) are loaded securely from environment variables, not hardcoded.
-   **Structured Data Summarization:** The LLM receives structured JSON data back from the tool and is prompted to perform calculations and provide a coherent, human-readable summary.

## Core Components

-   `blockfrost_server.py`: The MCP server. It loads the OpenAPI spec and handles the actual API calls to Blockfrost.
-   `blockfrost_client.py`: The client application. It takes a user prompt, communicates with the LLM and the MCP server, and displays the final result.
-   `blockfrost_openapi.yaml`: A curated OpenAPI specification defining the four Blockfrost endpoints that are exposed as tools.

## Requirements

-   Python 3.8+
-   `uv` (for package management, can be installed with `pip install uv`)
-   A Blockfrost Project ID
-   An Anthropic (Claude) API Key

## Setup and Installation

**1. Clone the Repository**

```bash
git clone <your-repo-url>
cd mcp-blockfrost-llm
```

**2. Set Up Environment Variables**

This project requires two secret keys to function. It is critical to set them as environment variables for security.

Create a file named `.env` in the project root:
```
BLOCKFROST_PROJECT_ID="mainnet..."
ANTHROPIC_API_KEY="sk-ant-..."
```
Then, source this file into your terminal session:
```bash
source .env
```
_Alternatively, you can export them directly in your terminal for the current session:_
```bash
export BLOCKFROST_PROJECT_ID="YOUR_BLOCKFROST_PROJECT_ID"
export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
```

**3. Install Dependencies with `uv`**

This project uses `uv` for fast and reproducible dependency management. The `uv.lock` file ensures you install the exact versions of the packages used during development.

```bash
# This will create a virtual environment and install dependencies from uv.lock
uv sync
```

## Running the Application

The server and client must be run in separate terminal windows.

**Step 1: Start the MCP Server**

In your first terminal, activate the virtual environment and start the server. It will wait for requests from the client.

```bash
# Activate the virtual environment if not already active
source .venv/bin/activate 

# Start the server
python blockfrost_server.py
```
You should see output indicating the server has started and loaded 4 tools.

**Step 2: Run the Client**

In a **second terminal**, activate the virtual environment and run the client script.

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the client to send a prompt to the LLM
python blockfrost_client.py
```
The client will print the entire interaction, including the tool call, the API result, and the final, summarized response from Claude.

## How It Works

1.  The **Client** sends a natural language prompt (e.g., "What are the totals for address X?") and the list of available tools to the **LLM (Claude)**.
2.  The **LLM** analyzes the prompt, selects the appropriate tool (`get_address_totals`), and generates the required parameters (`address: "..."`).
3.  The **Client** receives this tool call request and forwards it to the **MCP Server**.
4.  The **MCP Server** validates the call and makes a secure, authenticated request to the real **Blockfrost API**.
5.  The **Blockfrost API** returns the blockchain data as JSON.
6.  The **MCP Server** passes this data back to the **Client**.
7.  The **Client** sends the structured JSON data back to the **LLM**, asking it to provide a final summary.
8.  The **LLM** analyzes the raw data, performs calculations (like converting Lovelace to ADA), and generates a final, human-friendly answer, which the client prints.
