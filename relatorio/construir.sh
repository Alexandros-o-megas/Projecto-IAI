#!/usr/bin/env sh
# Gera o relatório: .docx (python-docx sobre o template oficial) e depois, no
# LibreOffice sem interface, actualiza campos e índices e exporta o PDF.
#   sh relatorio/construir.sh
set -e
cd "$(dirname "$0")/.."
P="$(pwd)"
PY="${PYTHON:-$P/.venv/bin/python}"
mkdir -p relatorio/lo_perfil/user/Scripts/python
cp relatorio/macro/actualizar.py relatorio/lo_perfil/user/Scripts/python/
"$PY" relatorio/diagrama.py
"$PY" relatorio/gerar_relatorio.py
DOC_IN="$P/outputs/Relatorio_Grupo06_P6.docx" \
DOCX_OUT="$P/outputs/Relatorio_Grupo06_P6.docx" \
PDF_OUT="$P/outputs/Relatorio_Grupo06_P6.pdf" \
libreoffice -env:UserInstallation="file://$P/relatorio/lo_perfil" --headless --norestore \
  'vnd.sun.star.script:actualizar.py$actualizar?language=Python&location=user'
echo "PDF: $P/outputs/Relatorio_Grupo06_P6.pdf"
