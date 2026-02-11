{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.file  # provides libmagic
    pkgs.git
  ];

  shellHook = ''
    # Set library path for libmagic on macOS
    export DYLD_LIBRARY_PATH="${pkgs.file}/lib''${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"

    # Activate Python venv if it exists
    if [ -f .venv/bin/activate ]; then
      source .venv/bin/activate
    fi
  '';
}
