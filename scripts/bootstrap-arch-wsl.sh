#!/usr/bin/env bash
# Set up Ninurta on Arch Linux (WSL2). Safe to re-run:
#   ./scripts/bootstrap-arch-wsl.sh
# The PDFs are laid out by Typst, which comes with the Python packages: no TeX to install.
set -euo pipefail

if ! grep -qi arch /etc/os-release; then
  echo "This script targets Arch Linux." >&2; exit 1
fi

PKGS=(
  adobe-source-sans-fonts    # the resume font (Source Sans 3)
  poppler                    # pdftotext / pdfinfo (page count, `make text`)
  python python-pip make git
)
# For editing cv/*.typ, a Typst language server helps: tinymist (AUR or `cargo install`).

echo "==> Updating system and installing packages"
sudo pacman -Syu --needed --noconfirm "${PKGS[@]}"
fc-cache -f >/dev/null

echo "==> Python packages (typst, pydantic, ...)"
pip install --user -r "$(dirname "$0")/../requirements.txt" || \
  pip install --user --break-system-packages -r "$(dirname "$0")/../requirements.txt"

cat <<'MSG'

Done. Next:
  cd ~/resume && make        # builds pdf/resume-en.pdf and pdf/resume-fr.pdf
  make watch LANG_=en        # rebuild on every save
  make view LANG_=en         # open the PDF in your Windows default viewer

Windows path to this repo: \\wsl.localhost\<distro>\home\<user>\resume  (distro name: `wsl -l` in PowerShell)
MSG
