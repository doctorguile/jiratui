#!/bin/bash
# Patches python-magic in uv tools to find libmagic from nix profile
# Run this after: uv tool install jiratui
#
# Prerequisites:
#   nix profile install nixpkgs#file

LOADER_FILE="$HOME/.local/share/uv/tools/jiratui/lib/python3.12/site-packages/magic/loader.py"

if [[ ! -f "$LOADER_FILE" ]]; then
    echo "Error: $LOADER_FILE not found"
    echo "Make sure jiratui is installed via: uv tool install jiratui"
    exit 1
fi

if grep -q 'nix-profile' "$LOADER_FILE"; then
    echo "Patch already applied"
    exit 0
fi

# Add nix profile path to the search paths
sed -i.bak "s|'/opt/homebrew/lib',|'/opt/homebrew/lib',\\
      os.path.expanduser('~/.nix-profile/lib'),  # nix profile support|" "$LOADER_FILE"

if grep -q 'nix-profile' "$LOADER_FILE"; then
    echo "Patch applied successfully"
    rm -f "${LOADER_FILE}.bak"
else
    echo "Error: Failed to apply patch"
    mv "${LOADER_FILE}.bak" "$LOADER_FILE"
    exit 1
fi
