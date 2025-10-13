#!/bin/bash
set -e

PROTO_DIR="analyzer/proto"
mkdir -p "$PROTO_DIR"

echo "📥 Fetching protocol buffers from lightwallet-protocol (main branch)..."

# Clone main branch
TEMP_DIR=$(mktemp -d)
git clone https://github.com/zcash/lightwallet-protocol.git "$TEMP_DIR"

echo "On branch: $(git -C "$TEMP_DIR" branch --show-current)"

# Copy proto files from walletrpc directory (using absolute paths)
cp "$TEMP_DIR/walletrpc/compact_formats.proto" "$PROTO_DIR/"
cp "$TEMP_DIR/walletrpc/service.proto" "$PROTO_DIR/"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Proto files updated in $PROTO_DIR (main branch)"
ls -la "$PROTO_DIR"
