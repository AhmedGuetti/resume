-- Drop into ~/.config/nvim/lua/plugins/latex.lua (lazy.nvim spec)
-- vimtex: compile with latexmk (uses the repo's .latexmkrc) + texlab for LSP.
return {
  {
    "lervag/vimtex",
    lazy = false, -- vimtex must not be lazy-loaded
    init = function()
      vim.g.vimtex_compiler_method = "latexmk"
      vim.g.vimtex_compiler_latexmk = { out_dir = "build", aux_dir = "build", options = { "-synctex=1" } }
      -- Open the PDF in Windows (SumatraPDF if it's the default .pdf handler)
      vim.g.vimtex_view_method = "general"
      vim.g.vimtex_view_general_viewer = "wslview"
      vim.g.vimtex_quickfix_mode = 0
    end,
  },
  {
    "neovim/nvim-lspconfig",
    config = function()
      vim.lsp.config("texlab", {
        settings = { texlab = { chktex = { onOpenAndSave = true }, build = { onSave = false } } },
      })
      vim.lsp.enable("texlab")
    end,
  },
}
