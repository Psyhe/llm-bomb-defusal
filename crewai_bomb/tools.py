from typing import ClassVar
from crewai.tools import BaseTool
from pydantic import Field, BaseModel
import asyncio
from game_mcp.game_client import Defuser, Expert


class DefuserToolInput(BaseModel):
    command: str = Field(..., description="Command to send to the Defuser, like 'cut wire 1' or 'state'")

    model_config = {
        "extra": "allow"
    }


class DefuserTool(BaseTool):
    def __init__(self, server_url: str):
        super().__init__(
            name="Defuser Tool",
            description="Tool to send commands to the bomb defuser",
            args_schema=DefuserToolInput
        )
        self._defuser_client = Defuser()
        self._server_url = server_url
        self._initialized = False

    async def _ensure_connection(self):
        if not self._initialized:
            await self._defuser_client.connect_to_server(self._server_url)
            self._initialized = True

    async def _arun(self, command: str) -> str:
        await self._ensure_connection()
        return await self._defuser_client.run(command)

    def run(self, command: str) -> str:
        return asyncio.run(self._arun(command))

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous _run is not supported. Use 'run' method instead.")
    
class ExpertToolInput(BaseModel):
    dummy_input: str = Field(..., description="Just pass any string to get the bomb manual")

    model_config = {
        "extra": "allow"
    }


class ExpertTool(BaseTool):
    def __init__(self, server_url: str):
        super().__init__(
            name="Expert Tool",
            description="Tool to fetch bomb manual information for solving modules",
            args_schema=ExpertToolInput
        )
        self._expert_client = Expert()
        self._server_url = server_url
        self._initialized = False

    async def _ensure_connection(self):
        if not self._initialized:
            await self._expert_client.connect_to_server(self._server_url)
            self._initialized = True

    async def _arun(self, dummy_input: str) -> str:
        await self._ensure_connection()
        return await self._expert_client.run()

    def run(self, dummy_input: str) -> str:
        return asyncio.run(self._arun(dummy_input))

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous _run is not supported. Use 'run' method instead.")
