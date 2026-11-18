#!/usr/bin/env bash
# Bootstrap a LaTeX toolchain for the resume repo on Arch Linux (WSL2).
# Safe to re-run. Usage:
#   ./scripts/bootstrap-arch-wsl.sh          # standard install (~600 MB)
#   ./scripts/bootstrap-arch-wsl.sh --full   # + texlive-fontsextra (~1.5 GB more fonts)
set -euo pipefail

FULL=0
[[ "${1:-}" == "--full" ]] && FULL=1

if ! grep -qi arch /etc/os-release; then
  echo "This script targets Arch Linux." >&2; exit 1
fi

PKGS=(
  # TeX Live (Arch splits it into collections)
  texlive-basic texlive-bin texlive-latex texlive-latexrecommended
  texlive-latexextra texlive-fontsrecommended texlive-luatex texlive-xetex
  texlive-binextra           # latexmk, chktex, latexindent, synctex
  texlive-langfrench texlive-langenglish
  # latexindent's Perl deps
  perl-yaml-tiny perl-file-homedir
  # Editor tooling
  texlab                     # LaTeX language server (Neovim, VS Code, etc.)
  poppler                    # pdftotext / pdfinfo (used by make text / check)
  make git
)
(( FULL )) && PKGS+=(texlive-fontsextra)

echo "==> Updating system and installing packages"
sudo pacman -Syu --needed --noconfirm "${PKGS[@]}"

echo "==> Building font caches"
fc-cache -f >/dev/null
luaotfload-tool -u >/dev/null 2>&1 || true

echo "==> Versions"
lualatex --version | head -1
latexmk -v | head -2 | tail -1
texlab --version || true

cat <<'EOF'

Done. Next:
  cd ~/resume && make        # builds pdf/resume-en.pdf and pdf/resume-fr.pdf
  make watch LANG_=en        # rebuild on every save
  make view LANG_=en         # open the PDF in your Windows default viewer

Windows path to this repo: \\wsl.localhost\<distro>\home\<user>\resume  (distro name: `wsl -l` in PowerShell)
EOF
