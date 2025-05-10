from crewai.tools import BaseTool


from crewai.tools import BaseTool
from pydantic import Field, BaseModel, ConfigDict
import asyncio

# Assuming you already have BombClient, Defuser, and Expert classes imported
from game_mpc import Defuser, Expert

class DefuserToolInput(BaseModel):
    """Schema for Defuser tool input."""
    command: str = Field(..., description="Command to send to the Defuser, like 'cut wire 1' or 'state'")

    model_config = {
        "extra": "allow"
    }

class DefuserTool(BaseTool):
    name = "Defuser Tool"
    description = "Tool to send commands to the bomb defuser"
    args_schema = DefuserToolInput

    def __init__(self, server_url: str):
        super().__init__()
        self.defuser_client = Defuser()
        self.server_url = server_url
        self._initialized = False

    async def _ensure_connection(self):
        if not self._initialized:
            await self.defuser_client.connect_to_server(self.server_url)
            self._initialized = True

    async def _arun(self, command: str) -> str:
        await self._ensure_connection()
        result = await self.defuser_client.run(command)
        return result

    def run(self, command: str) -> str:
        """Sync wrapper for CrewAI"""
        return asyncio.run(self._arun(command))


class ExpertToolInput(BaseModel):
    """Schema for Expert tool input."""
    dummy_input: str = Field(..., description="Just pass any string to get the bomb manual")

    model_config = {
        "extra": "allow"
    }

class ExpertTool(BaseTool):
    name = "Expert Tool"
    description = "Tool to fetch bomb manual information for solving modules"
    args_schema = ExpertToolInput

    def __init__(self, server_url: str):
        super().__init__()
        self.expert_client = Expert()
        self.server_url = server_url
        self._initialized = False

    async def _ensure_connection(self):
        if not self._initialized:
            await self.expert_client.connect_to_server(self.server_url)
            self._initialized = True

    async def _arun(self, dummy_input: str) -> str:
        await self._ensure_connection()
        result = await self.expert_client.run()
        return result

    def run(self, dummy_input: str) -> str:
        """Sync wrapper for CrewAI"""
        return asyncio.run(self._arun(dummy_input))