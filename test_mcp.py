import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import base64

# Define the server command
# Note: Using sys.executable to ensure we use the same python env
server_params = StdioServerParameters(
    command=sys.executable,
    args=["src/openscad_mcp/server.py"],
)

async def main():
    print("Starting client...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Test render_views
            scad_code = "cube([10, 20, 30], center=true);"
            print("\nTesting render_views...")
            result = await session.call_tool("render_views", arguments={"scad_code": scad_code})
            
            if result.content and result.content[0].type == "text":
                # Check if it looks like base64
                b64_data = result.content[0].text
                if len(b64_data) > 100:
                    print(f"Success! Received base64 image (length: {len(b64_data)})")
                    # Save for verification
                    with open("test_output.png", "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    print("Saved to test_output.png")
                else:
                    print(f"Output unexpected: {b64_data}")
            else:
                print(f"Failed to render: {result}")

            # Test export_stl
            print("\nTesting export_stl...")
            result = await session.call_tool("export_stl", arguments={"scad_code": scad_code, "output_filename": "test_cube.stl"})
            print(f"Result: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
