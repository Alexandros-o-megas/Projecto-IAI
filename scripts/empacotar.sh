#!/usr/bin/env sh
# Cria IA_PROJECTO_GRUPO_06_LAB.zip com o repositório completo (incluindo .git),
# CSV, gráficos e relatório. Executar na raiz do repositório.
set -e
NOME=IA_PROJECTO_GRUPO_06_LAB
DEST="${1:-..}"
git status --short | grep -q . && echo "Aviso: há alterações por commitar." || true
rm -f "$DEST/$NOME.zip"
zip -rq "$DEST/$NOME.zip" . -x '.venv/*' '*__pycache__*' '.pytest_cache/*' '*.pyc' 'relatorio/lo_perfil/*'
echo "Criado $DEST/$NOME.zip"
unzip -l "$DEST/$NOME.zip" | tail -n 1
