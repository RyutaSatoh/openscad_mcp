import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import base64
import os

async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_render.py <scad_file>")
        sys.exit(1)

    scad_file = sys.argv[1]
    with open(scad_file, "r") as f:
        scad_code = f.read()

    # Use existing venv python
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["src/openscad_mcp/server.py"],
        env=os.environ.copy() # Pass current env (including DISPLAY)
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print(f"Rendering {scad_file}...")
            result = await session.call_tool("render_views", arguments={"scad_code": scad_code})
            
            if result.content and result.content[0].type == "text":
                b64_data = result.content[0].text
                output_filename = scad_file.replace(".scad", ".png")
                with open(output_filename, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                print(f"Saved visualization to {output_filename}")
            else:
                print(f"Failed to render: {result}")

if __name__ == "__main__":
    asyncio.run(main())
