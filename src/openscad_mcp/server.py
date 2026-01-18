from mcp.server.fastmcp import FastMCP
import subprocess
import tempfile
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import io
import base64

mcp = FastMCP("openscad-mcp")

def run_openscad(scad_code: str, output_extension: str, args: list[str] = None) -> bytes:
    """Run openscad with the given code and arguments, returning the output file bytes."""
    if args is None:
        args = []

    with tempfile.TemporaryDirectory() as tmpdir:
        scad_path = os.path.join(tmpdir, "input.scad")
        out_path = os.path.join(tmpdir, f"output.{output_extension}")
        
        with open(scad_path, "w") as f:
            f.write(scad_code)
            
        cmd = ["openscad", "-o", out_path] + args + [scad_path]
        
        try:
            # Run openscad. Capture output for debugging if needed.
            # Add DISPLAY=:0 to environment for rendering
            env = os.environ.copy()
            if "DISPLAY" not in env:
                env["DISPLAY"] = ":0"

            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            print(f"DEBUG: OpenSCAD stdout: {result.stdout}", file=sys.stderr)
            print(f"DEBUG: OpenSCAD stderr: {result.stderr}", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"DEBUG: OpenSCAD failed. Stdout: {e.stdout}", file=sys.stderr)
            print(f"DEBUG: OpenSCAD failed. Stderr: {e.stderr}", file=sys.stderr)
            raise RuntimeError(f"OpenSCAD failed:\nStdout: {e.stdout}\nStderr: {e.stderr}")
            
        if not os.path.exists(out_path):
             raise RuntimeError("OpenSCAD did not produce an output file.")
             
        with open(out_path, "rb") as f:
            return f.read()

@mcp.tool()
def render_views(scad_code: str) -> str:
    """
    Renders the OpenSCAD code into a composite image containing 4 views:
    Top, Front, Right, and Isometric.
    Returns the image data as a base64 encoded string.
    """
    # Define camera rotations for different views
    # Format: transx,transy,transz,rotx,roty,rotz,distance
    # We use distance=0 + --autocenter --viewall to handle scaling automatically
    
    # Note: OpenSCAD camera logic can be tricky. 
    # Standard Z-up assumptions:
    # Top: Looking down Z. rot=(0,0,0)
    # Front: Looking forward Y (or -Y). rot=(90, 0, 0)
    # Right: Looking X. rot=(90, 0, 90)
    # Iso: Diagonal. rot=(60, 0, 45)
    
    # Restore 4-view layout with corrected rotations and orthographic projection
    # Top: 0,0,0
    # Front: 90,0,0
    # Right: 90,0,90
    # Iso: 60,0,45
    
    common_args = ["--projection=o", "--viewall", "--autocenter"]
    
    views = [
        ("Top",   [f"--camera=0,0,0,0,0,0,0"] + common_args),
        ("Front", [f"--camera=0,0,0,90,0,0,0"] + common_args),
        ("Right", [f"--camera=0,0,0,90,0,90,0"] + common_args),
        ("Iso",   [f"--camera=0,0,0,60,0,45,0"] + common_args),
    ]
    
    images = []
    
    try:
        for name, args in views:
            # Generate 500x500 for each view
            img_bytes = run_openscad(scad_code, "png", args + ["--imgsize=500,500", "--colorscheme=Tomorrow Night"])
            img = Image.open(io.BytesIO(img_bytes))
            
            # Add label
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            
            draw.text((10, 10), name, fill="white", font=font)
            images.append(img)
            
        # Combine images into a 2x2 grid
        w, h = images[0].size
        grid_img = Image.new('RGB', (w * 2, h * 2))
        
        grid_img.paste(images[0], (0, 0))      # Top
        grid_img.paste(images[1], (w, 0))      # Front
        grid_img.paste(images[2], (0, h))      # Right
        grid_img.paste(images[3], (w, h))      # Iso
        
        # Convert to base64
        buf = io.BytesIO()
        grid_img.save(buf, format="PNG")
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        return b64_str
        
    except Exception as e:
        return f"Error rendering views: {str(e)}"

@mcp.tool()
def export_stl(scad_code: str, output_filename: str = "output.stl") -> str:
    """
    Exports the OpenSCAD code to an STL file.
    The file is saved in the current working directory.
    """
    try:
        stl_bytes = run_openscad(scad_code, "stl")
        
        # Ensure output filename ends with .stl
        if not output_filename.lower().endswith(".stl"):
            output_filename += ".stl"
            
        with open(output_filename, "wb") as f:
            f.write(stl_bytes)
            
        return f"Successfully exported STL to {output_filename}"
    except Exception as e:
        return f"Error exporting STL: {str(e)}"

if __name__ == "__main__":
    mcp.run()
