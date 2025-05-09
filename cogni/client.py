# client.py
import sys
import subprocess
import json
import uuid

def send_jsonrpc_request(server_process, method, params=None):
    """Send a JSON-RPC request to the server process and return the response."""
    request_id = str(uuid.uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {}
    }
    
    # Send the request to the server
    request_json = json.dumps(request) + "\n"
    server_process.stdin.write(request_json.encode())
    server_process.stdin.flush()
    
    # Read the response from the server
    response_json = server_process.stdout.readline().decode().strip()
    try:
        response = json.loads(response_json)
        if "error" in response:
            raise Exception(f"JSON-RPC error: {response['error']}")
        return response.get("result")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON response: {response_json}")

def main():
    print("Starting MCP client...")
    
    try:
        # Start the server process
        print("Starting server process...")
        server_process = subprocess.Popen(
            ["python", "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,  # Line buffered
            universal_newlines=False  # Binary mode
        )
        
        # Initialize the server
        print("Initializing server...")
        init_result = send_jsonrpc_request(server_process, "initialize", {
            "capabilities": {}
        })
        print(f"Server initialized: {init_result}")
        
        # Call the "add" tool
        print("Calling 'add' tool with a=5, b=3...")
        add_result = send_jsonrpc_request(server_process, "callTool", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        print(f"Result of 5 + 3 = {add_result}")
        
        # Read the greeting resource
        print("Reading 'greeting://World' resource...")
        greeting_result = send_jsonrpc_request(server_process, "readResource", {
            "uri": "greeting://World"
        })
        print(f"Greeting: {greeting_result}")
        
        # Shutdown the server
        print("Shutting down server...")
        send_jsonrpc_request(server_process, "shutdown")
        
        # Exit the server
        print("Exiting server...")
        send_jsonrpc_request(server_process, "exit")
        
        # Wait for the server to exit
        server_process.wait(timeout=5)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        
        # Try to kill the server process if it's still running
        try:
            server_process.kill()
        except:
            pass

if __name__ == "__main__":
    main()
