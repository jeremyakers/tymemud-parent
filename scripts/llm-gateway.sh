#!/bin/bash
# Wrapper script to run the LLM Gateway MCP server
# This ensures proper working directory and Python path

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# The project root is the parent of scripts/
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to llm_gateway directory
 cd "$PROJECT_ROOT/llm_gateway" || exit 1

# Set Python path to include the llm_gateway module
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the MCP server
exec python3 -m llm_gateway.server
