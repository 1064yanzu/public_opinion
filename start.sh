#!/bin/bash
# Data Analysis System - Unix Launcher
# Supports Linux and macOS

set -e

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  echo "Usage: ./start.sh [command]"
  echo
  echo "Commands:"
  echo "  setup    - Run initial setup"
  echo "  start    - Start the server"
  echo "  test     - Run tests"
  echo "  status   - Check system status"
  echo "  help     - Show this help message"
  exit 0
fi

python3 launcher.py "$@"
