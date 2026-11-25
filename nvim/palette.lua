-- cinnamon-palettes: Neovim follows the desktop palette.
-- `palette apply <slug>` writes ~/.config/nvim/colors/palette.lua and runs
-- `:colorscheme palette` in every running Neovim; new instances start with it.
-- Symlinked into ~/.config/nvim/lua/plugins/ by `install.sh`.
---@type LazySpec
return {
  { "AstroNvim/astroui", opts = { colorscheme = "palette" } },
  { "folke/tokyonight.nvim", lazy = true, opts = { style = "night" } },
  { "catppuccin/nvim", name = "catppuccin", lazy = true },
  { "rebelot/kanagawa.nvim", lazy = true },
  { "sainnhe/everforest", lazy = true },
  { "ellisonleao/gruvbox.nvim", lazy = true },
  { "gbprod/nord.nvim", lazy = true },
  { "rose-pine/neovim", name = "rose-pine", lazy = true },
  { "RRethy/base16-nvim", lazy = true },
}
