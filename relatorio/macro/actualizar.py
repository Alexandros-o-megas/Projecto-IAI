import os
import uno
from com.sun.star.beans import PropertyValue


def _pv(nome, valor):
    p = PropertyValue()
    p.Name, p.Value = nome, valor
    return p


def actualizar(*args):
    entrada = os.environ["DOC_IN"]
    desktop = XSCRIPTCONTEXT.getDesktop()
    doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(entrada), "_blank", 0, (_pv("Hidden", True),))
    for _ in range(2):  # 2 passagens: os números de página mudam depois do 1.º update
        doc.getTextFields().refresh()
        indices = doc.getDocumentIndexes()
        for i in range(indices.getCount()):
            indices.getByIndex(i).update()
    doc.storeToURL(uno.systemPathToFileUrl(os.environ["DOCX_OUT"]), (_pv("FilterName", "MS Word 2007 XML"),))
    doc.storeToURL(uno.systemPathToFileUrl(os.environ["PDF_OUT"]), (_pv("FilterName", "writer_pdf_Export"),))
    doc.close(True)
