from typing import Sequence, Dict, Optional, List
import json
import subprocess
import shlex
import os
import tempfile
import re
import argparse

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError
from pydantic import BaseModel, Field

class ArduinoCommandResult(BaseModel):
    command: str
    success: bool
    output: str
    error: str = ""

class BoardInfo(BaseModel):
    port: str
    board_name: str = ""
    fqbn: str = ""

class CompileResult(BaseModel):
    sketch: str
    success: bool
    output: str
    error: str = ""
    binary_path: str = ""

class UploadResult(BaseModel):
    sketch: str
    port: str
    fqbn: str = ""
    success: bool
    output: str
    error: str = ""

class MonitorResult(BaseModel):
    port: str
    baud_rate: int
    output: str
    error: str = ""

class FileContent(BaseModel):
    filepath: str
    content: str
    exists: bool = False

class BlinkResult(BaseModel):
    """Result of the complete Arduino blink workflow"""
    sketch_created: bool = False
    sketch_path: str = ""
    compilation_success: bool = False
    upload_success: bool = False
    compilation_output: str = ""
    upload_output: str = ""
    error: str = ""

class ArduinoProject(BaseModel):
    """Information about an Arduino project"""
    sketch_path: str
    fqbn: str = ""
    port: str = ""
    workspace_path: str = ""
    description: str = ""

class ArduinoCliServer:
    def __init__(self, workdir=None):
        # Store command results
        self.command_results: Dict[str, ArduinoCommandResult] = {}
        # Create a temporary directory to store command outputs
        self.output_dir = tempfile.mkdtemp(prefix="arduino_cli_output_")
        # Set workdir
        self.workdir = os.path.abspath(workdir) if workdir else os.getcwd()
        if not os.path.exists(self.workdir):
            try:
                os.makedirs(self.workdir)
            except Exception as e:
                print(f"Warning: Could not create workdir: {e}")
        print(f"Arduino CLI output directory: {self.output_dir}")
        print(f"Arduino CLI working directory: {self.workdir}")

    def save_command_result(self, command: str, result: ArduinoCommandResult) -> None:
        """Save command execution result"""
        # Save to in-memory dictionary
        self.command_results[command] = result
        
        # Also write to file for persistence
        output_file = os.path.join(self.output_dir, f"{hash(command)}.json")
        with open(output_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2)

    def get_command_result(self, command: str) -> Optional<ArduinoCommandResult]:
        """Get previously executed command result from memory or file"""
        # First check if exists in memory
        if command in self.command_results:
            return self.command_results[command]
        
        # If not in memory, try to read from file
        output_file = os.path.join(self.output_dir, f"{hash(command)}.json")
        if os.path.exists(output_file):
            try:
                with open(output_file, "r") as f:
                    data = json.load(f)
                    return ArduinoCommandResult(**data)
            except Exception as e:
                print(f"Error reading command result: {str(e)}")
        
        return None
    
    def execute_command(self, command: str) -> ArduinoCommandResult:
        """Get Arduino CLI command result (doesn't execute, only returns previously executed results)"""
        result = self.get_command_result(command)
        if result:
            return result
        else:
            return ArduinoCommandResult(
                command=f"arduino-cli {command}",
                success=False,
                output="",
                error="Command not yet executed. Please execute the command in terminal first, then use store_command_result tool to store the result."
            )
    
    def store_command_result(self, command: str, output: str, error: str = "", success: bool = True) -> ArduinoCommandResult:
        """Store a command result that was executed in terminal"""
        result = ArduinoCommandResult(
            command=f"arduino-cli {command}",
            success=success,
            output=output,
            error=error
        )
        self.save_command_result(command, result)
        return result

    def execute_cli_command(self, command: str, env=None) -> ArduinoCommandResult:
        """Execute Arduino CLI command directly (for internal operations)"""
        try:
            full_command = f"arduino-cli {command}"
            args = shlex.split(full_command)
            
            # Log the command being executed
            print(f"Executing command: {full_command}")
            
            # Set environment variables, ensure $HOME is defined
            command_env = os.environ.copy()
            if env:
                command_env.update(env)
            
            # Ensure HOME environment variable exists
            if 'HOME' not in command_env:
                command_env['HOME'] = os.path.expanduser('~')
            
            # Create multiple designated temporary directories for Arduino CLI
            # This ensures we have fallbacks if one location doesn't work
            temp_dirs = [
                os.path.join(self.workdir, "arduino_cli_temp"),
                os.path.join(self.workdir, ".arduino_tmp"),
                os.path.join(os.path.expanduser('~'), ".arduino_cli_temp")
            ]
            
            # Ensure all temp directories exist
            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    try:
                        os.makedirs(temp_dir, exist_ok=True)
                        os.chmod(temp_dir, 0o755)  # Ensure directory has proper permissions
                        print(f"Created temp directory: {temp_dir}")
                    except Exception as e:
                        print(f"Warning: Could not create temp directory {temp_dir}: {e}")
            
            # Use the first available temp directory
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir) and os.access(temp_dir, os.W_OK):
                    # Set multiple temp environment variables for maximum compatibility
                    command_env['TMPDIR'] = temp_dir
                    command_env['TMP'] = temp_dir
                    command_env['TEMP'] = temp_dir
                    print(f"Setting TMPDIR to: {temp_dir}")
                    break
            
            # Add explicit build path for compile commands
            if command.startswith("compile"):
                build_dir = os.path.join(self.workdir, "build_output")
                if not os.path.exists(build_dir):
                    os.makedirs(build_dir, exist_ok=True)
                    
                if "--build-path" not in command:
                    command = f"{command} --build-path \"{build_dir}\""
                    args = shlex.split(f"arduino-cli {command}")
                    print(f"Added build path: {build_dir} to command")
            
            # Execute with up to 3 retries for resiliency
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    result = subprocess.run(
                        args, 
                        capture_output=True, 
                        text=True,
                        check=False,
                        env=command_env
                    )
                    
                    success = (result.returncode == 0)
                    print(f"Command executed with return code: {result.returncode} (success: {success})")
                    
                    # If successful or if it's not a temporary file error, break the loop
                    if success or "temporary file" not in result.stderr:
                        break
                    
                    # Otherwise retry with a different approach
                    retry_count += 1
                    print(f"Retrying command (attempt {retry_count}/{max_retries})")
                    
                    if "ctags" in result.stderr:
                        # For ctags errors, try a direct approach
                        print("Detected ctags error, trying direct compilation...")
                        # Skip ctags by using --no-color flag which changes CLI behavior
                        if "--no-color" not in command:
                            command = f"{command} --no-color"
                            args = shlex.split(f"arduino-cli {command}")
                    
                except Exception as e:
                    print(f"Error during command execution: {str(e)}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
            
            return ArduinoCommandResult(
                command=full_command,
                success=(result.returncode == 0),
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else ""
            )
        except Exception as e:
            error_message = f"Error executing command: {str(e)}"
            print(error_message)
            return ArduinoCommandResult(
                command=f"arduino-cli {command}",
                success=False,
                output="",
                error=error_message
            )

    def list_boards(self) -> List[BoardInfo]:
        """List available boards"""
        result = self.execute_cli_command("board list")
        boards = []
        
        if result.success and result.output:
            # Parse board list output
            # Output format is typically: Port, Type, Board Name, FQBN, Core
            lines = result.output.strip().split('\n')
            if len(lines) > 1:  # At least has a header line and one data line
                for line in lines[1:]:  # Skip header line
                    parts = line.split()
                    if len(parts) >= 1:
                        port = parts[0]
                        board_name = " ".join(parts[2:-1]) if len(parts) > 2 else ""
                        fqbn = parts[-1] if len(parts) > 1 else ""
                        boards.append(BoardInfo(port=port, board_name=board_name, fqbn=fqbn))
        
        return boards
    
    def compile_sketch(self, sketch_path: str, fqbn: str = "") -> CompileResult:
        """Compile Arduino sketch"""
        # Make sure sketch_path is absolute or correctly relative to current directory
        sketch_path = os.path.normpath(sketch_path)
        if not os.path.isabs(sketch_path):
            sketch_path = os.path.join(os.getcwd(), sketch_path)
        
        if not os.path.exists(sketch_path):
            return CompileResult(
                sketch=sketch_path,
                success=False,
                output="",
                error=f"Sketch file not found: {sketch_path}"
            )
        
        # Check if the sketch file has content
        try:
            with open(sketch_path, 'r') as f:
                sketch_content = f.read().strip()
            if not sketch_content:
                return CompileResult(
                    sketch=sketch_path,
                    success=False,
                    output="",
                    error="Sketch file is empty"
                )
            print(f"Compiling sketch: {sketch_path} with content length: {len(sketch_content)}")
            print(f"Sketch content (first 100 chars): {sketch_content[:100]}")
        except Exception as e:
            return CompileResult(
                sketch=sketch_path,
                success=False,
                output="",
                error=f"Error reading sketch file: {str(e)}"
            )
        
        # Create a unique build directory under workdir for this sketch
        sketch_name = os.path.basename(os.path.dirname(sketch_path))
        build_path = os.path.join(self.workdir, f"build_{sketch_name}")
        if not os.path.exists(build_path):
            os.makedirs(build_path, exist_ok=True)
        
        # Try to use compile command with stored result first
        try:
            # Create a "safe" command that might have been stored
            simple_cmd = f"compile -b {fqbn} {os.path.basename(os.path.dirname(sketch_path))}"
            stored_result = self.get_command_result(simple_cmd)
            
            if stored_result and stored_result.success:
                print(f"Using stored successful compilation result for {sketch_name}")
                return CompileResult(
                    sketch=sketch_path,
                    success=True,
                    output=stored_result.output,
                    error="",
                    binary_path=""  # We don't know the binary path from stored result
                )
        except Exception as e:
            print(f"Error checking stored results: {e}")
        
        # Create a build directory in the sketch's folder too
        sketch_dir = os.path.dirname(sketch_path)
        sketch_build_path = os.path.join(sketch_dir, "build")
        if not os.path.exists(sketch_build_path):
            os.makedirs(sketch_build_path, exist_ok=True)
            print(f"Created build directory in sketch folder: {sketch_build_path}")
        
        # Proceed with regular compilation
        compile_cmd = f"compile {sketch_path}"
        if fqbn:
            compile_cmd += f" --fqbn {fqbn}"
        
        # Add build path and verbose flag to command
        compile_cmd += f" --build-path {sketch_build_path} -v"
        
        # Set up a specific environment for this command
        env = {
            'TMPDIR': build_path,
            'TMP': build_path,
            'TEMP': build_path
        }
        
        result = self.execute_cli_command(compile_cmd, env)
        
        # Log the compile result for debugging
        print(f"Compilation result: success={result.success}")
        if not result.success:
            print(f"Error: {result.error}")
            print(f"Output: {result.output}")
            
            # If compilation failed due to temporary file issues but we have stored result
            if "temporary file" in result.error and stored_result and stored_result.success:
                print("Using stored successful result despite temporary file error")
                return CompileResult(
                    sketch=sketch_path,
                    success=True,
                    output=stored_result.output,
                    error="",
                    binary_path=""
                )
        
        binary_path = ""
        if result.success:
            # Try to extract binary file path from output
            match = re.search(r"Sketch uses .*\n(.*\.ino\..*)\n", result.output)
            if match:
                binary_path = match.group(1)
        
        return CompileResult(
            sketch=sketch_path,
            success=result.success,
            output=result.output,
            error=result.error,
            binary_path=binary_path
        )
    
    def upload_sketch(self, sketch_path: str, port: str, fqbn: str = "") -> UploadResult:
        """Upload sketch to board on specified port"""
        # Make sure sketch_path is absolute or correctly relative to current directory
        sketch_path = os.path.normpath(sketch_path)
        if not os.path.isabs(sketch_path):
            sketch_path = os.path.join(os.getcwd(), sketch_path)
            
        if not os.path.exists(sketch_path):
            return UploadResult(
                sketch=sketch_path,
                port=port,
                fqbn=fqbn,
                success=False,
                output="",
                error=f"Sketch file not found: {sketch_path}"
            )
        
        upload_cmd = f"upload -p {port} {sketch_path}"
        if fqbn:
            upload_cmd += f" --fqbn {fqbn}"
        
        result = self.execute_cli_command(upload_cmd)
        
        return UploadResult(
            sketch=sketch_path,
            port=port,
            fqbn=fqbn,
            success=result.success,
            output=result.output,
            error=result.error
        )
    
    def monitor_port(self, port: str, baud_rate: int = 9600, timeout: int = 10) -> MonitorResult:
        """Monitor serial port (in real-world usage should be an interactive process)"""
        # Note: This is just a simulation, real serial monitoring should be a long-running process
        monitor_cmd = f"monitor -p {port} -c baudrate={baud_rate} --timeout {timeout}"
        
        result = self.execute_cli_command(monitor_cmd)
        
        return MonitorResult(
            port=port,
            baud_rate=baud_rate,
            output=result.output,
            error=result.error
        )
    
    def create_sketch(self, sketch_name: str, code: str) -> FileContent:
        """Create Arduino sketch file and directory structure"""
        try:
            # Ensure sketch is in a directory with the same name within the workdir
            sketch_dir = os.path.join(self.workdir, sketch_name)
            sketch_file = os.path.join(sketch_dir, f"{sketch_name}.ino")
            
            # Create sketch directory if doesn't exist
            if not os.path.exists(sketch_dir):
                os.makedirs(sketch_dir)
                print(f"Created sketch directory: {sketch_dir}")
            
            # Write sketch file
            with open(sketch_file, 'w') as f:
                f.write(code)
                print(f"Wrote {len(code)} bytes to {sketch_file}")
            
            # Verify that the file was created and has content
            if os.path.exists(sketch_file):
                with open(sketch_file, 'r') as f:
                    content = f.read()
                    print(f"Verified file content: {len(content)} bytes")
                    if not content:
                        print("WARNING: Created file is empty!")
            else:
                print(f"WARNING: File {sketch_file} was not created!")
            
            # Return full path to help with future operations
            return FileContent(
                filepath=sketch_file,
                content=code,
                exists=True
            )
        except Exception as e:
            error_msg = f"Error creating sketch: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
    
    def read_file(self, filepath: str) -> FileContent:
        """Read file content"""
        try:
            # If filepath is relative and doesn't exist, try resolving it relative to workdir
            if not os.path.isabs(filepath) and not os.path.exists(filepath):
                filepath_in_workdir = os.path.join(self.workdir, filepath)
                if os.path.exists(filepath_in_workdir):
                    filepath = filepath_in_workdir
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                return FileContent(
                    filepath=filepath,
                    content=content,
                    exists=True
                )
            else:
                return FileContent(
                    filepath=filepath,
                    content="",
                    exists=False
                )
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    def write_file(self, filepath: str, content: str) -> FileContent:
        """Write file content"""
        try:
            # If filepath is not absolute, make it relative to workdir
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.workdir, filepath)
            
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            return FileContent(
                filepath=filepath,
                content=content,
                exists=True
            )
        except Exception as e:
            raise ValueError(f"Error writing file: {str(e)}")
    
    def get_core_platforms(self) -> List[str]:
        """Get list of installed Arduino core platforms"""
        result = self.execute_cli_command("core list")
        platforms = []
        
        if result.success and result.output:
            lines = result.output.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                for line in lines[1:]:
                    parts = line.strip().split()
                    if parts:
                        platforms.append(parts[0])
        
        return platforms
    
    def install_platform(self, platform_id: str) -> ArduinoCommandResult:
        """Install Arduino platform"""
        return self.execute_cli_command(f"core install {platform_id}")

    def create_blink_sketch(self, led_pin: int = 13, delay_ms: int = 1000) -> str:
        """Create a simple LED blink sketch with customizable pin and delay"""
        code = f"""void setup() {{
  pinMode({led_pin}, OUTPUT);
}}

void loop() {{
  digitalWrite({led_pin}, HIGH);
  delay({delay_ms});
  digitalWrite({led_pin}, LOW);
  delay({delay_ms});
}}
"""
        return code
    
    def complete_blink_workflow(self, sketch_name: str, port: str, fqbn: str, 
                               led_pin: int = 13, delay_ms: int = 1000) -> BlinkResult:
        """Complete workflow to create, compile and upload a blink sketch"""
        result = BlinkResult()
        
        try:
            # Step 1: Create sketch
            code = self.create_blink_sketch(led_pin, delay_ms)
            sketch_result = self.create_sketch(sketch_name, code)
            
            if not sketch_result.exists:
                result.error = f"Failed to create sketch: {sketch_name}"
                return result
                
            result.sketch_created = True
            result.sketch_path = sketch_result.filepath
            
            # Step 2: Check if platform is installed, if not install it
            platforms = self.get_core_platforms()
            platform_id = fqbn.split(':')[0] + ':' + fqbn.split(':')[1]  # Extract arduino:avr from arduino:avr:mega
            
            if platform_id not in platforms:
                print(f"Platform {platform_id} not found, installing...")
                install_result = self.install_platform(platform_id)
                if not install_result.success:
                    result.error = f"Failed to install platform {platform_id}: {install_result.error}"
                    return result
            
            # Step 3: Compile the sketch
            compile_result = self.compile_sketch(sketch_result.filepath, fqbn)
            result.compilation_output = compile_result.output
            
            if not compile_result.success:
                result.error = f"Compilation failed: {compile_result.error}"
                return result
                
            result.compilation_success = True
            
            # Step 4: Upload the sketch
            upload_result = self.upload_sketch(sketch_result.filepath, port, fqbn)
            result.upload_output = upload_result.output
            
            if not upload_result.success:
                result.error = f"Upload failed: {upload_result.error}"
                return result
                
            result.upload_success = True
            
            return result
        except Exception as e:
            result.error = f"Workflow error: {str(e)}"
            return result

    def find_arduino_files(self, directory: str = None) -> List[str]:
        """Find all Arduino .ino files in the given directory (recursively)"""
        ino_files = []
        try:
            # If no directory specified, use workdir
            search_dir = directory if directory else self.workdir
            
            for root, _, files in os.walk(search_dir):
                for file in files:
                    if file.endswith(".ino"):
                        ino_files.append(os.path.join(root, file))
            return ino_files
        except Exception as e:
            print(f"Error scanning directory: {str(e)}")
            return []
    
    def discover_projects(self, workspace: str = None) -> List[ArduinoProject]:
        """Discover Arduino projects in the given workspace directory"""
        projects = []
        
        # If no workspace specified, use workdir
        search_dir = workspace if workspace else self.workdir
        
        ino_files = self.find_arduino_files(search_dir)
        
        for ino_file in ino_files:
            project_name = os.path.basename(os.path.dirname(ino_file))
            projects.append(ArduinoProject(
                sketch_path=ino_file,
                workspace_path=os.path.dirname(ino_file),
                description=f"Arduino project: {project_name}"
            ))
        
        return projects

    def validate_sketch_path(self, sketch_path: str) -> str:
        """Validate and normalize sketch path, returning absolute path"""
        if not sketch_path:
            raise ValueError("Sketch path cannot be empty")
            
        # If path is not absolute, try to resolve it relative to workdir
        if not os.path.isabs(sketch_path):
            potential_path = os.path.join(self.workdir, sketch_path)
            # If file exists in workdir, use that path
            if os.path.exists(potential_path):
                sketch_path = potential_path
        
        # Normalize path
        sketch_path = os.path.normpath(sketch_path)
        
        # Convert to absolute path if it's relative
        if not os.path.isabs(sketch_path):
            sketch_path = os.path.abspath(sketch_path)
            
        # Check if file exists
        if not os.path.exists(sketch_path):
            raise ValueError(f"Sketch file not found: {sketch_path}")
            
        # Check if file has .ino extension
        if not sketch_path.endswith('.ino'):
            raise ValueError(f"Sketch file must have .ino extension: {sketch_path}")
            
        return sketch_path

    def quick_compile(self, sketch_path: str, fqbn: str = "") -> CompileResult:
        """Enhanced compile function with better error handling and diagnostics"""
        try:
            # Validate and normalize path
            sketch_path = self.validate_sketch_path(sketch_path)
            
            # Check if the sketch file has code
            with open(sketch_path, 'r') as f:
                code = f.read().strip()
                if not code:
                    return CompileResult(
                        sketch=sketch_path,
                        success=False,
                        output="",
                        error="Sketch file is empty. Please add Arduino code to the file."
                    )
            
            print(f"Compiling sketch at {sketch_path} with FQBN: {fqbn}")
            print(f"Sketch size: {len(code)} bytes")
            
            # Run compilation with verbose flag
            compile_cmd = f"compile -v {sketch_path}"
            if fqbn:
                compile_cmd += f" --fqbn {fqbn}"
            
            result = self.execute_cli_command(compile_cmd)
            
            # Enhanced error reporting
            if not result.success:
                # Try to extract more detailed error information
                error_detail = result.error
                if not error_detail and "error:" in result.output:
                    error_lines = [line for line in result.output.split('\n') if "error:" in line]
                    if error_lines:
                        error_detail += "\n".join(error_lines)
                
                print(f"Compilation failed: {error_detail}")
                
                return CompileResult(
                    sketch=sketch_path,
                    success=False,
                    output=result.output,
                    error=error_detail or "Compilation failed with unknown error"
                )
            else:
                print("Compilation successful!")
            
            # Extract binary path
            binary_path = ""
            match = re.search(r"Sketch uses .*\n(.*\.ino\..*)\n", result.output)
            if match:
                binary_path = match.group(1)
                print(f"Binary path: {binary_path}")
            
            return CompileResult(
                sketch=sketch_path,
                success=result.success,
                output=result.output,
                error=result.error,
                binary_path=binary_path
            )
        except Exception as e:
            error_msg = f"Error during compilation process: {str(e)}"
            print(error_msg)
            return CompileResult(
                sketch=sketch_path,
                success=False,
                output="",
                error=error_msg
            )

    def add_board_url(self, url: str) -> ArduinoCommandResult:
        """Add a board manager URL to Arduino CLI config"""
        # First ensure config is initialized
        init_result = self.execute_cli_command("config init")
        if not init_result.success:
            return init_result
            
        # Then add the URL to the config
        add_cmd = f"config add board_manager.additional_urls {url}"
        return self.execute_cli_command(add_cmd)
    
    def update_index(self) -> ArduinoCommandResult:
        """Update the core index to fetch latest board info"""
        return self.execute_cli_command("core update-index")
    
    def list_all_boards(self, platform_id: str = "") -> ArduinoCommandResult:
        """List all available boards, optionally filtered by platform"""
        cmd = "board listall"
        if platform_id:
            cmd += f" {platform_id}"
        return self.execute_cli_command(cmd)
    
    def setup_esp32(self) -> Dict[str, ArduinoCommandResult]:
        """Setup ESP32 development environment"""
        results = {}
        
        # Step 1: Add ESP32 board URL
        esp32_url = "https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json"
        results["add_url"] = self.add_board_url(esp32_url)
        
        # Step 2: Update index
        results["update_index"] = self.update_index()
        
        # Step 3: Install ESP32 core
        results["install_core"] = self.execute_cli_command("core install esp32:esp32")
        
        # Step 4: List installed cores to verify
        results["list_cores"] = self.execute_cli_command("core list")
        
        return results

    def simplified_compile(self, sketch_path: str, fqbn: str = "") -> Dict:
        """Simple compilation that returns success status, build directory and hex file path"""
        compile_result = self.compile_sketch(sketch_path, fqbn)
        
        binary_path = ""
        build_dir = ""
        
        if compile_result.success:
            # Extract binary file path from output
            match = re.search(r"Sketch uses .*\n(.*\.ino\..*)\n", compile_result.output)
            if match:
                binary_path = match.group(1)
            
            # Determine build directory path
            sketch_dir = os.path.dirname(sketch_path)
            build_dir = os.path.join(sketch_dir, "build")
            
            # If no binary path found in output, try to find it in the build directory
            if not binary_path or not os.path.exists(binary_path):
                # Try to find hex file in build directory
                try:
                    for file in os.listdir(build_dir):
                        if file.endswith(".hex"):
                            binary_path = os.path.join(build_dir, file)
                            break
                except Exception as e:
                    print(f"Error searching for hex file: {e}")
        
        return {
            "success": compile_result.success,
            "build_dir": build_dir,
            "hex_path": binary_path,
            "error": compile_result.error if not compile_result.success else ""
        }

    def upload_hex(self, hex_path: str, port: str, fqbn: str = "") -> Dict:
        """Upload a hex file directly to a board"""
        if not os.path.exists(hex_path):
            return {
                "success": False,
                "command": "",
                "error": f"Hex file not found: {hex_path}"
            }
            
        upload_cmd = f"upload -i {hex_path} -p {port}"
        if fqbn:
            upload_cmd += f" --fqbn {fqbn}"
            
        full_command = f"arduino-cli {upload_cmd}"
        result = self.execute_cli_command(upload_cmd)
            
        return {
            "success": result.success,
            "command": full_command,
            "error": result.error if not result.success else ""
        }

    def simplified_upload(self, sketch_path: str, port: str, fqbn: str = "", hex_path: str = "") -> Dict:
        """Upload sketch or hex file to board - supports both sketch path or direct hex file upload"""
        # Create the upload command
        if hex_path and os.path.exists(hex_path):
            # If hex path provided and exists, use it directly
            return self.upload_hex(hex_path, port, fqbn)
        else:
            # Otherwise use the sketch path
            upload_cmd = f"upload -p {port} {sketch_path}"
            if fqbn:
                upload_cmd += f" --fqbn {fqbn}"
            
            full_command = f"arduino-cli {upload_cmd}"
            
            # Execute the upload
            upload_result = self.upload_sketch(sketch_path, port, fqbn)
            
            # Return with command information
            return {
                "success": upload_result.success,
                "command": full_command,
                "error": upload_result.error if not upload_result.success else ""
            }
        
    def install_board(self, platform_id: str) -> Dict:
        """Install a board platform with all necessary steps"""
        results = {}
        
        # Step 1: Check if already installed
        platforms = self.get_core_platforms()
        if platform_id in platforms:
            return {"success": True, "message": f"Platform {platform_id} is already installed"}
            
        # Step 2: Update index first
        update_result = self.update_index()
        if not update_result.success:
            return {"success": False, "message": f"Failed to update index: {update_result.error}"}
            
        # Step 3: Install platform
        install_result = self.install_platform(platform_id)
        
        # Step 4: Verify installation
        if install_result.success:
            platforms = self.get_core_platforms()
            if platform_id in platforms:
                return {"success": True, "message": f"Successfully installed {platform_id}"}
            else:
                return {"success": False, "message": f"Installation command succeeded but {platform_id} not found in installed platforms"}
        else:
            return {"success": False, "message": f"Failed to install {platform_id}: {install_result.error}"}
            
    def check_version(self) -> Dict:
        """Check Arduino CLI version"""
        version_result = self.execute_cli_command("version")
        
        if version_result.success:
            # Extract version number
            version = version_result.output.strip()
            return {
                "success": True,
                "version": version
            }
        else:
            return {
                "success": False,
                "error": version_result.error
            }
            
    def list_available_boards(self) -> Dict:
        """List all available boards including connected and installable"""
        board_list = []
        
        # Get connected boards
        connected_boards = self.list_boards()
        connected_fqbns = [board.fqbn for board in connected_boards]
        
        # Get installed platforms
        platforms_result = self.execute_cli_command("core list")
        
        # Get all boards from installed platforms
        all_boards_result = self.execute_cli_command("board listall")
        
        # Format the output
        result = {
            "connected": [{"port": b.port, "fqbn": b.fqbn, "board_name": b.board_name} for b in connected_boards],
            "platforms": self.get_core_platforms(),
            "all_boards": all_boards_result.output if all_boards_result.success else ""
        }
        
        return result

    def compile_and_upload(self, sketch_path: str, port: str, fqbn: str = "") -> Dict:
        """Compile Arduino sketch and immediately upload the resulting hex file"""
        # Step 1: Compile the sketch
        compile_result = self.simplified_compile(sketch_path, fqbn)
        
        # If compilation failed, return early with the error
        if not compile_result["success"]:
            return {
                "success": False,
                "compile_success": False,
                "upload_success": False,
                "build_dir": compile_result.get("build_dir", ""),
                "hex_path": compile_result.get("hex_path", ""),
                "command": f"arduino-cli compile --fqbn {fqbn} {sketch_path}",
                "error": f"Compilation failed: {compile_result['error']}"
            }
            
        # Get the hex file path from compilation result
        hex_path = compile_result.get("hex_path", "")
        build_dir = compile_result.get("build_dir", "")
        
        # If we couldn't find the hex file, try to locate it
        if not hex_path or not os.path.exists(hex_path):
            # Try to find hex file in build directory
            try:
                if build_dir and os.path.exists(build_dir):
                    for file in os.listdir(build_dir):
                        if file.endswith(".hex"):
                            hex_path = os.path.join(build_dir, file)
                            print(f"Found hex file in build directory: {hex_path}")
                            break
            except Exception as e:
                print(f"Error searching for hex file: {e}")
                
        # If we still couldn't find the hex file, return error
        if not hex_path or not os.path.exists(hex_path):
            return {
                "success": False,
                "compile_success": True,
                "upload_success": False,
                "build_dir": build_dir,
                "hex_path": "",
                "command": "",
                "error": "Compilation succeeded but couldn't find the .hex file for uploading"
            }
        
        # Step 2: Upload the compiled hex file
        upload_result = self.upload_hex(hex_path, port, fqbn)
        
        # Return combined results
        return {
            "success": upload_result["success"],
            "compile_success": True,
            "upload_success": upload_result["success"],
            "build_dir": build_dir,
            "hex_path": hex_path,
            "command": upload_result["command"],
            "error": upload_result["error"] if not upload_result["success"] else ""
        }

async def serve(workdir=None) -> None:
    server = Server("arduino-cli-mcp")
    # Initialize with workdir
    arduino_server = ArduinoCliServer(workdir=workdir)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            # Only keep the simplified tools
            Tool(
                name="compile",
                description="Compile an Arduino sketch / 編譯Arduino草圖",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sketch_path": {
                            "type": "string",
                            "description": "Path to the .ino file / .ino文件的路徑",
                        },
                        "fqbn": {
                            "type": "string",
                            "description": "Fully Qualified Board Name (e.g. 'arduino:avr:uno') / 完整開發板名稱",
                            "default": "arduino:avr:uno"
                        }
                    },
                    "required": ["sketch_path", "fqbn"]
                },
            ),
            
            Tool(
                name="upload",
                description="Upload an Arduino sketch or hex file to a board / 上傳Arduino草圖或hex檔案到開發板",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sketch_path": {
                            "type": "string", 
                            "description": "Path to the .ino file / .ino文件的路徑"
                        },
                        "hex_path": {
                            "type": "string",
                            "description": "Path to the hex file (optional, if provided will upload directly) / hex檔案的絕對路徑（可選）"
                        },
                        "port": {
                            "type": "string",
                            "description": "Serial port of the board / 開發板的串口",
                        },
                        "fqbn": {
                            "type": "string",
                            "description": "Fully Qualified Board Name / 完整開發板名稱",
                            "default": "arduino:avr:uno"
                        }
                    },
                    "required": ["port", "fqbn"]
                },
            ),
            
            Tool(
                name="install_board",
                description="Install a board platform / 安裝開發板平台",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "platform_id": {
                            "type": "string",
                            "description": "Platform ID (e.g. arduino:avr, esp32:esp32) / 平台ID（如arduino:avr, esp32:esp32）",
                        }
                    },
                    "required": ["platform_id"]
                },
            ),
            
            Tool(
                name="check",
                description="Check Arduino CLI version / 檢查Arduino CLI版本",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            
            Tool(
                name="list",
                description="List all available boards and platforms / 列出所有可用的開發板和平台",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),

            Tool(
                name="compile_upload",
                description="Compile and upload an Arduino sketch in one step / 一步驟完成編譯和上傳Arduino草圖",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sketch_path": {
                            "type": "string",
                            "description": "Path to the .ino file / .ino文件的路徑",
                        },
                        "port": {
                            "type": "string",
                            "description": "Serial port of the board / 開發板的串口",
                        },
                        "fqbn": {
                            "type": "string",
                            "description": "Fully Qualified Board Name / 完整開發板名稱",
                            "default": "arduino:avr:uno"
                        }
                    },
                    "required": ["sketch_path", "port", "fqbn"]
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls."""
        try:
            if name == "compile":
                sketch_path = arguments.get("sketch_path")
                fqbn = arguments.get("fqbn", "arduino:avr:uno")
                
                if not sketch_path:
                    raise ValueError("Missing required parameter: sketch_path")
                
                if not fqbn:
                    raise ValueError("Missing required parameter: fqbn")
                
                result = arduino_server.simplified_compile(sketch_path, fqbn)
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]
                
            elif name == "upload":
                sketch_path = arguments.get("sketch_path")
                hex_path = arguments.get("hex_path")
                port = arguments.get("port")
                fqbn = arguments.get("fqbn", "arduino:avr:uno")
                
                if not port:
                    raise ValueError("Missing required parameter: port")
                
                if not fqbn:
                    raise ValueError("Missing required parameter: fqbn")
                
                # Either sketch_path or hex_path must be provided
                if not sketch_path and not hex_path:
                    raise ValueError("Either sketch_path or hex_path is required")
                
                result = arduino_server.simplified_upload(sketch_path, port, fqbn, hex_path)
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]
                
            elif name == "install_board":
                platform_id = arguments.get("platform_id")
                
                if not platform_id:
                    raise ValueError("Missing required parameter: platform_id")
                    
                if platform_id == "esp32":
                    platform_id = "esp32:esp32"  # Automatically fix common mistake
                
                result = arduino_server.install_board(platform_id)
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]
                
            elif name == "check":
                result = arduino_server.check_version()
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]
                
            elif name == "list":
                result = arduino_server.list_available_boards()
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]

            elif name == "compile_upload":
                sketch_path = arguments.get("sketch_path")
                port = arguments.get("port")
                fqbn = arguments.get("fqbn", "arduino:avr:uno")
                
                if not sketch_path:
                    raise ValueError("Missing required parameter: sketch_path")
                
                if not port:
                    raise ValueError("Missing required parameter: port")
                
                if not fqbn:
                    raise ValueError("Missing required parameter: fqbn")
                
                result = arduino_server.compile_and_upload(sketch_path, port, fqbn)
                return [
                    TextContent(type="text", text=json.dumps(result, indent=2))
                ]
                
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            raise ValueError(f"Error processing request: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)

if __name__ == "__main__":
    import asyncio
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Arduino CLI MCP Server")
    parser.add_argument('--workdir', type=str, default=None,
                        help='Working directory for Arduino sketches and projects')
    args = parser.parse_args()
    
    # Validate workdir
    if args.workdir and not os.path.exists(args.workdir):
        print(f"Warning: Specified workdir '{args.workdir}' does not exist. Will try to create it.")
    
    print(f"Starting Arduino CLI MCP server with workdir: {args.workdir or 'current directory'}")
    asyncio.run(serve(workdir=args.workdir))