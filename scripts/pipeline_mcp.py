"""Call the local pipeline over real MCP STDIO, not direct Python dispatch.
Usage: python scripts/pipeline_mcp.py create_job '{"video_type": ...}'
"""
import asyncio
from datetime import timedelta
import json
import time
import os
from pathlib import Path
import sys
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession


async def call(name, arguments):
    started=time.monotonic()
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(Path(__file__).resolve().parents[1])
    params=StdioServerParameters(command=sys.executable,args=['-m','ai_video_pipeline.mcp.server'],env=env)
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            result=await session.call_tool(name,arguments=arguments,read_timeout_seconds=timedelta(hours=2))
            if result.isError: raise RuntimeError(result.content)
            data=json.loads(result.content[0].text)
            data['mcp_elapsed_seconds']=round(time.monotonic()-started,3)
            return data


if __name__=='__main__':
    argument=sys.argv[2]
    args=json.loads(Path(argument[1:]).read_text() if argument.startswith('@') else argument)
    print(json.dumps(asyncio.run(call(sys.argv[1],args)),indent=2))
