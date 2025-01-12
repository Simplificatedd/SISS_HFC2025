class CvConverter:
    def __init__(self, cv_file):
        """
        Initialize the converter with the CV file.

        Args:
            cv_file (str): The path to the CV document.
        """
        self.cv_file = cv_file

    def convert_to_text(self):
        """
        Convert the CV document to plain text.

        Returns:
            str: The converted text.
        """
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        return converter.convert(self.cv_file)

    def export_to_markdown(self, cv_text):
        """
        Export the CV text to Markdown format.

        Args:
            cv_text (str): The plain text of the CV document.

        Returns:
            str: The Markdown representation of the CV document.
        """

        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        return cv_text.document.export_to_markdown()