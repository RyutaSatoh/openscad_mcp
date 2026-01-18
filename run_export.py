import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_export.py <scad_file> [output_stl]")
        sys.exit(1)

    scad_file = sys.argv[1]
    output_stl = sys.argv[2] if len(sys.argv) > 2 else scad_file.replace(".scad", ".stl")

    with open(scad_file, "r") as f:
        scad_code = f.read()

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["src/openscad_mcp/server.py"],
        env=os.environ.copy()
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print(f"Exporting {scad_file} to {output_stl}...")
            result = await session.call_tool("export_stl", arguments={
                "scad_code": scad_code,
                "output_filename": output_stl
            })
            
            if result.content and result.content[0].type == "text":
                print(f"Server response: {result.content[0].text}")
            else:
                print(f"Failed to export: {result}")

if __name__ == "__main__":
    asyncio.run(main())
