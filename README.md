# cinnamon-palettes

Omarchy-style theme switching for Linux Mint Cinnamon. One click (or `palette apply <slug>`)
switches the whole desktop to a palette:

| Target | What changes |
|---|---|
| Cinnamon / GTK3 / GTK4 / window borders | `~/.themes/Palette-<Name>`, recoloured from Mint-Y-Dark with an Omarchy-flavoured overlay (flat surfaces, thin outlines, accent highlights) |
| libadwaita apps | `~/.config/gtk-4.0` symlink is repointed (only if it already is a symlink) |
| Wallpaper | generated per palette: dusk sky, accent sun, layered ridges |
| Ghostty | `~/.config/ghostty/themes/palette-current`, live-reloaded with SIGUSR2 |
| btop | `~/.config/btop/themes/palette.theme` (picked up on next start) |
| Neovim (AstroNvim) | `colorscheme palette`; running instances recolour live over their RPC sockets |

Palettes: Tokyo Night, Catppuccin Mocha, Kanagawa, Everforest, Gruvbox, Nord, Rosé Pine,
Osaka Jade, Matte Black. Neovim uses the upstream colourscheme where one exists and
base16-nvim generated from the palette otherwise.

## Install

    ./install.sh

Then add the **Palettes** applet to a panel. Hotkey: <kbd>Super</kbd>+<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Space</kbd>
opens the picker (a "next palette" hotkey can be set in the applet settings).

## CLI

    palette list | current | apply SLUG | next | prev | build [SLUG|--all] | restore

The first `apply` snapshots your current themes, wallpaper, Ghostty config, btop theme and
Neovim scheme to `~/.local/state/cinnamon-palettes/snapshot.json`; `palette restore` puts them back.

## Adding a palette

Drop a JSON file in `palettes/` (copy an existing one): surfaces `bg_dark`, `bg`, `bg_alt`,
`outline`, text `fg`, `fg_dim`, `accent`, `accent2`, 16 `ansi` colours, optional
`success`/`error`/`warning`, and `nvim` (`{plugin, colorscheme}` or `{base16: true}`).
Themes rebuild automatically when the palette or build files change.

## Credits

Palettes from their upstream projects (Tokyo Night, Catppuccin, Kanagawa, Everforest, Gruvbox,
Nord, Rosé Pine) and Omarchy (Osaka Jade, Matte Black). Themes derive from Mint-Y; GPL-3.0-or-later.
