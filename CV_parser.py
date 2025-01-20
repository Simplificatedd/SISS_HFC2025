import fitz  # PyMuPDF

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
            str: The extracted text from the CV.
        """
        text = ""
        try:
            # Open the PDF file
            with fitz.open(self.cv_file) as doc:
                # Iterate through pages and extract text
                for page in doc:
                    text += page.get_text()
        except Exception as e:
            raise RuntimeError(f"Error processing the file: {e}")
        return text

    def export_to_markdown(self, cv_text):
        """
        Export the CV text to Markdown format.

        Args:
            cv_text (str): The plain text of the CV document.

        Returns:
            str: The Markdown representation of the CV document.
        """
        # Simple Markdown conversion
        markdown = f"# CV Document\n\n{cv_text}"
        return markdown
