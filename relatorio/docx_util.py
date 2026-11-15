"""Utilitários python-docx para preencher o template oficial (estilos do template)."""
import copy
import re

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


MONO = "Courier New"   # existe no Windows; no Linux o LibreOffice usa Liberation Mono (mesmas métricas)


class Escritor:
    def __init__(self, doc):
        self.doc = doc

    # ---------------------------------------------------------------- texto
    def _runs(self, par, texto):
        """Suporta **negrito**, ~itálico~ e `código`; um * isolado é literal (A*, h*)."""
        for parte in re.split(r"(\*\*.+?\*\*|~[^~]+~|`[^`]+`)", texto):
            if not parte:
                continue
            if parte.startswith("**"):
                par.add_run(parte[2:-2]).bold = True
            elif parte.startswith("`"):
                r = par.add_run(parte[1:-1])
                r.font.name = MONO
                r.font.size = Pt(10)
            elif parte.startswith("~") and len(parte) > 2:
                par.add_run(parte[1:-1]).italic = True
            else:
                par.add_run(parte)
        return par

    def h1(self, t):
        return self.doc.add_paragraph(t, style="Heading 1")

    def h2(self, t):
        return self.doc.add_paragraph(t, style="Heading 2")

    def h3(self, t):
        return self.doc.add_paragraph(t, style="Heading 3")

    def p(self, texto, alinhar=True):
        par = self._runs(self.doc.add_paragraph(style="Normal"), texto)
        if alinhar:
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return par

    def lista(self, itens, numerada=False):
        for i, t in enumerate(itens, 1):
            par = self.doc.add_paragraph(style="List Paragraph")
            self._runs(par, (f"{i}. " if numerada else "• ") + t)
            par.paragraph_format.left_indent = Cm(0.8)
            par.paragraph_format.first_line_indent = Cm(-0.5)

    def codigo(self, texto, tamanho=8.5):
        for linha in texto.strip("\n").split("\n"):
            par = self.doc.add_paragraph(style="Normal")
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.space_before = Pt(0)
            par.paragraph_format.line_spacing = 1.0
            par.paragraph_format.first_line_indent = Cm(0)
            r = par.add_run(linha if linha else " ")
            r.font.name = MONO
            r._element.rPr.rFonts.set(qn("w:eastAsia"), MONO)
            r.font.size = Pt(tamanho)
        self.doc.add_paragraph(style="Normal")

    def quebra(self):
        from docx.enum.text import WD_BREAK
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------------------------------------------------------------- legendas
    def legenda(self, tipo, texto):
        """Legenda com campo SEQ (actualizável no índice de figuras/tabelas)."""
        par = self.doc.add_paragraph(style="Caption1")
        par.add_run(f"{tipo} ")
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), f" SEQ {tipo} \\* ARABIC ")
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        self._n = getattr(self, "_n", {})
        self._n[tipo] = self._n.get(tipo, 0) + 1
        t.text = str(self._n[tipo])
        r.append(t)
        fld.append(r)
        par._p.append(fld)
        par.add_run(f" – {texto}")
        return par

    # ---------------------------------------------------------------- tabelas
    def tabela(self, legenda, cabecalho, linhas, larguras=None, tamanho=9):
        self.legenda("Tabela", legenda)
        t = self.doc.add_table(rows=1, cols=len(cabecalho))
        t.style = "Table Grid"
        for c, texto in zip(t.rows[0].cells, cabecalho):
            c.text = ""
            r = c.paragraphs[0].add_run(str(texto))
            r.bold = True
            r.font.size = Pt(tamanho)
            sombra = OxmlElement("w:shd")
            sombra.set(qn("w:val"), "clear")
            sombra.set(qn("w:fill"), "D9D9D9")
            c._tc.get_or_add_tcPr().append(sombra)
        for linha in linhas:
            cells = t.add_row().cells
            for c, texto in zip(cells, linha):
                c.text = ""
                self._runs(c.paragraphs[0], str(texto)).runs
                for r in c.paragraphs[0].runs:
                    r.font.size = Pt(tamanho)
        for row in t.rows:
            for c in row.cells:
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                pf = c.paragraphs[0].paragraph_format
                pf.first_line_indent = Cm(0)
                pf.space_after = Pt(0)
                pf.line_spacing = 1.0
        if larguras:
            for row in t.rows:
                for c, w in zip(row.cells, larguras):
                    c.width = Cm(w)
        self.doc.add_paragraph(style="Normal")
        return t

    def figura(self, caminho, legenda, largura=15):
        par = self.doc.add_paragraph(style="Normal")
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.first_line_indent = Cm(0)
        par.add_run().add_picture(str(caminho), width=Cm(largura))
        self.legenda("Figura", legenda)


def substituir(par, novo):
    """Substitui o texto de um parágrafo mantendo a formatação do 1.º run."""
    if not par.runs:
        par.add_run(novo)
        return
    par.runs[0].text = novo
    for r in par.runs[1:]:
        r.text = ""


def remover(el):
    el.getparent().remove(el)


def clonar_antes(el, ref):
    novo = copy.deepcopy(el)
    ref.addprevious(novo)
    return novo
