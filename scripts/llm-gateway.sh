#!/bin/bash
# Wrapper script to run the LLM Gateway MCP server
# This ensures proper working directory and Python path
#
# Environment Variables:
#   BUILDERPORT_HOST - BuilderPort host (default: 127.0.0.1)
#   BUILDERPORT_PORT - BuilderPort port (default: 9697, which is status port)
#   BUILDERPORT_TOKEN - Auth token (default: read from lib/etc/builderport.token)
#
# The game server runs on port 9696, status port is 9697

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# The project root is the parent of scripts/
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to llm_gateway directory
 cd "$PROJECT_ROOT/llm_gateway" || exit 1

# Set Python path to include the llm_gateway module
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Default to port 9697 (status port = game port 9696 + 1)
export BUILDERPORT_PORT="${BUILDERPORT_PORT:-9697}"
export BUILDERPORT_HOST="${BUILDERPORT_HOST:-127.0.0.1}"

# Run the MCP server
exec python3 -m llm_gateway.server
