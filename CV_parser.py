from docling.document_converter import DocumentConverter

CV_FILE = "CV.docx"
source = CV_FILE
converter = DocumentConverter()
cv_text = converter.convert(source)
cv_markdown = cv_text.document.export_to_markdown()

# To be continued...