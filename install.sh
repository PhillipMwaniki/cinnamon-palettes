#!/bin/sh
# Install cinnamon-palettes for the current user (idempotent).
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$HOME/.local/bin" "$HOME/.local/share/cinnamon/applets"
ln -sfn "$ROOT/palette" "$HOME/.local/bin/palette"
ln -sfn "$ROOT/applet/palettes@PhillipMwaniki" "$HOME/.local/share/cinnamon/applets/palettes@PhillipMwaniki"

# Neovim follows the palette through a `palette` colorscheme
if [ -d "$HOME/.config/nvim/lua/plugins" ]; then
  ln -sfn "$ROOT/nvim/palette.lua" "$HOME/.config/nvim/lua/plugins/palette.lua"
  "$ROOT/palette" init-nvim
  nvim --headless "+Lazy! install" +qa >/dev/null 2>&1 || echo "note: run :Lazy install in Neovim"
fi

"$ROOT/palette" build --all
"$ROOT/palette" fetch || echo "note: photo wallpapers will download on first use"
echo "Installed. Add the 'Palettes' applet to a panel, or run: palette apply tokyo-night"
