# import asyncio


# # Feel free to import any libraries you need - if needed change requirements.txt
# import argparse
# from mcp import ClientSession
# from mcp.client.sse import sse_client


# class BombClient:
#     def __init__(self):
#         # YOUR CODE STARTS HERE
        
#         self.session = None

#         # YOUR CODE ENDS HERE

#     async def connect_to_server(self, server_url: str):
#         """Connect to an sse MCP server"""
#         # YOUR CODE STARTS HERE
        
#         print(f"Connecting to SSE server at {server_url}...")
        
#         self._streams_context = sse_client(url=server_url) 
#         streams = await self._streams_context.__aenter__()

#         self._session_context = ClientSession(*streams)
#         self.session: ClientSession = await self._session_context.__aenter__()
#         response = await self.session.list_tools()
#         tools = response.tools
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

#         print(f"Connected to MCP server at {server_url}")

#         # YOUR CODE ENDS HERE

#     async def process_query(self, tool_name: str, tool_args: dict[str, str]) -> str:
#         """Process a query using the game_interaction tool"""
#         # YOUR CODE STARTS HERE
        

#         # YOUR CODE ENDS HERE

#     async def cleanup(self):
#         """Properly clean up the session and streams"""
#         # YOUR CODE STARTS HERE
        
#         if self._session_context:
#             await self._session_context.__aexit__(None, None, None)
#         if self._streams_context:
#             await self._streams_context.__aexit__(None, None, None)

#         print("MCP client connection closed.")

#         # YOUR CODE ENDS HERE


# class Defuser(BombClient):
#     async def run(self, action: str) -> str:
#         """Run a defuser action"""
#         # YOUR CODE STARTS HERE

#         if not action:
#             action = input("Enter Defuser command (e.g., 'cut wire 1', 'hold', 'release on 3'): ")
#         response = await self.process_query("game_interaction", {"command": action})
#         print(response)
#         return response

    
#         # YOUR CODE ENDS HERE


# class Expert(BombClient):
#     async def run(self) -> str:
#         """Run an expert action"""
#         # YOUR CODE STARTS HERE
        
#         response = await self.process_query("get_manual", {})
#         print(response)
#         return response

#         # YOUR CODE ENDS HERE


# async def main():
#     """ Main function to connect to the server and run the clients """
#     # YOUR CODE STARTS HERE
    
#     import mcp.client
#     print(dir(mcp.client))

#     parser = argparse.ArgumentParser(description="MCP Bomb Client")
#     parser.add_argument("--url", required=True, help="Server URL (e.g., http://localhost:8080)")
#     parser.add_argument("--role", required=True, choices=["Defuser", "Expert"], help="Role to play")
#     args = parser.parse_args()

#     client = Defuser() if args.role == "Defuser" else Expert()
#     await client.connect_to_server(args.url)

#     try:
#         while True:
#             if args.role == "Defuser":
#                 await client.run()
#             else:
#                 await client.run()
#             await asyncio.sleep(0.1)
#     except KeyboardInterrupt:
#         print("🛑 Exiting client...")
#     finally:
#         await client.cleanup()


#     # YOUR CODE ENDS HERE


# async def expert_test(expert_client: Expert):
#     """Test the Expert class"""
#     result = await expert_client.run()

#     possible_outputs = ["BOOM!", "BOMB SUCCESSFULLY DISARMED!", "Regular Wires Module", "The Button Module",
#                         "Memory Module", "Simon Says Module"]

#     assert any(output.find(result) != -1 for output in possible_outputs), f"Expert test failed"


# async def defuser_test(defuser_client: Defuser):
#     """Test the Defuser class"""
#     result = await defuser_client.run("state")

#     possible_outputs = ["BOMB STATE"]

#     assert any(output.find(result) != -1 for output in possible_outputs), f"Defuser test failed"

# if __name__ == "__main__":
#     asyncio.run(main())
import asyncio

# Feel free to import any libraries you need - if needed change requirements.txt
import argparse
from mcp import ClientSession
from mcp.client.sse import sse_client


class BombClient:
    def __init__(self):
        # YOUR CODE STARTS HERE
        self.session = None
        self._session_context = None
        self._streams_context = None
        # YOUR CODE ENDS HERE

    async def connect_to_server(self, server_url: str):
        """Connect to an sse MCP server"""
        # YOUR CODE STARTS HERE
        print(f"Connecting to SSE server at {server_url}...")

        self._streams_context = sse_client(url=server_url)
        self._session_context = None

        streams = await self._streams_context.__aenter__()
        self._session_context = ClientSession(*streams)

        self.session = await self._session_context.__aenter__()
        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        print(f"Connected to MCP server at {server_url}")
        # YOUR CODE ENDS HERE

    async def process_query(self, tool_name: str, tool_args: dict[str, str]) -> str:
        """Process a query using the specified tool"""
        if not self.session:
            raise RuntimeError("Session is not initialized.")
        try:
            result = await self.session.call_tool(tool_name, tool_args)

            return result  # Ensure server tool returns {"result": "..."}
        except Exception as e:
            return f"Error processing query: {e}"

    async def cleanup(self):
        """Properly clean up the session and streams"""
        # YOUR CODE STARTS HERE
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)
        print("MCP client connection closed.")
        # YOUR CODE ENDS HERE


class Defuser(BombClient):
    async def run(self, action: str = "") -> str:
        """Run a defuser action"""
        # YOUR CODE STARTS HERE
        if not action:
            action = input("Enter Defuser command): ")
        response = await self.process_query("game_interaction", {"command": action})
        text = response.content[0].text
        print(text)
        return text
        # YOUR CODE ENDS HERE


class Expert(BombClient):
    async def run(self) -> str:
        """Run an expert action"""
        # YOUR CODE STARTS HERE
        response = await self.process_query("get_manual", {})
        text = response.content[0].text
        print(text)
        return text
        # YOUR CODE ENDS HERE


async def main():
    """ Main function to connect to the server and run the clients """
    # YOUR CODE STARTS HERE
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
            
            cont = input("Do you want to continue? (yes/no): ").strip().lower()
            if cont not in ["yes", "y"]:
                print("Exiting client loop...")
                break
    except KeyboardInterrupt:
        print("Exiting client...")
    finally:
        await client.cleanup()
    # YOUR CODE ENDS HERE

async def test_main():
    """ Main function to connect to the server and run the clients """
    # YOUR CODE STARTS HERE
    parser = argparse.ArgumentParser(description="MCP Bomb Client")
    parser.add_argument("--url", required=True, help="Server URL (e.g., http://localhost:8080)")
    parser.add_argument("--role", required=True, choices=["Defuser", "Expert"], help="Role to play")
    args = parser.parse_args()


    if args.role == "Defuser":
        client = Defuser()
        await client.connect_to_server(args.url)
        try:
            await defuser_test(client)
            print("Defuser test passed.")
        finally:
            await client.cleanup()
    else:
        client = Expert()
        await client.connect_to_server(args.url)
        try:
            await expert_test(client)
            print("Expert test passed.")
        finally:
            await client.cleanup()


async def expert_test(expert_client: Expert):
    """Test the Expert class"""
    result = await expert_client.run()

    possible_outputs = ["BOOM!", "BOMB SUCCESSFULLY DISARMED!", "Regular Wires Module", "The Button Module",
                        "Memory Module", "Simon Says Module"]

    assert any(output in result for output in possible_outputs), f"Expert test failed: got {result}"


async def defuser_test(defuser_client: Defuser):
    """Test the Defuser class"""
    result = await defuser_client.run("state")

    possible_outputs = ["BOMB STATE"]

    assert any(output in result for output in possible_outputs), f"Defuser test failed: got {result}"


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(test_main())
