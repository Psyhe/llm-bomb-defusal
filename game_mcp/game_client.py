import asyncio


# Feel free to import any libraries you need - if needed change requirements.txt
import argparse
from mcp import ClientSession
from mcp.client.sse import sse_client


class BombClient:
    def __init__(self):
        # YOUR CODE STARTS HERE
        
        self.sse_client = None
        self.session = None

        # YOUR CODE ENDS HERE

    async def connect_to_server(self, server_url: str):
        """Connect to an sse MCP server"""
        # YOUR CODE STARTS HERE
        
        print(f"Connecting to SSE server at {server_url}...")
        
        transport = AioHttpClientTransport(f"{server_url}/session_id/")
        self.client = McpClient(transport)
        await self.client.start()
        print(f"Connected to MCP server at {server_url}")

        # YOUR CODE ENDS HERE

    async def process_query(self, tool_name: str, tool_args: dict[str, str]) -> str:
        """Process a query using the game_interaction tool"""
        # YOUR CODE STARTS HERE
        
        try:
            result = await self.client.invoke_tool(tool_name, tool_args)
            return str(result)
        except Exception as e:
            return f"Error during MCP tool call: {e}"
        
        # YOUR CODE ENDS HERE

    async def cleanup(self):
        """Properly clean up the session and streams"""
        # YOUR CODE STARTS HERE
        
        if self.client:
            await self.client.aclose()
            print("🔌 MCP client connection closed.")

        # YOUR CODE ENDS HERE


class Defuser(BombClient):
    async def run(self, action: str) -> str:
        """Run a defuser action"""
        # YOUR CODE STARTS HERE

        if not action:
            action = input("Enter Defuser command (e.g., 'cut wire 1', 'hold', 'release on 3'): ")
        response = await self.process_query("game_interaction", {"command": action})
        print(response)
        return response

    
        # YOUR CODE ENDS HERE


class Expert(BombClient):
    async def run(self) -> str:
        """Run an expert action"""
        # YOUR CODE STARTS HERE
        
        response = await self.process_query("get_manual", {})
        print(response)
        return response

        # YOUR CODE ENDS HERE


async def main():
    """ Main function to connect to the server and run the clients """
    # YOUR CODE STARTS HERE
    
    import mcp.client
    print(dir(mcp.client))

    parser = argparse.ArgumentParser(description="MCP Bomb Client")
    parser.add_argument("--url", required=True, help="Server URL (e.g., http://localhost:8080)")
    parser.add_argument("--role", required=True, choices=["Defuser", "Expert"], help="Role to play")
    args = parser.parse_args()

    client = Defuser() if args.role == "Defuser" else Expert()
    await client.connect_to_server(args.url)

    try:
        while True:
            if args.role == "Defuser":
                await client.run()
            else:
                await client.run()
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("🛑 Exiting client...")
    finally:
        await client.cleanup()


    # YOUR CODE ENDS HERE


async def expert_test(expert_client: Expert):
    """Test the Expert class"""
    result = await expert_client.run()

    possible_outputs = ["BOOM!", "BOMB SUCCESSFULLY DISARMED!", "Regular Wires Module", "The Button Module",
                        "Memory Module", "Simon Says Module"]

    assert any(output.find(result) != -1 for output in possible_outputs), f"Expert test failed"


async def defuser_test(defuser_client: Defuser):
    """Test the Defuser class"""
    result = await defuser_client.run("state")

    possible_outputs = ["BOMB STATE"]

    assert any(output.find(result) != -1 for output in possible_outputs), f"Defuser test failed"

if __name__ == "__main__":
    asyncio.run(main())
