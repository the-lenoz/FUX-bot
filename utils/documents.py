import asyncio
import os
import tempfile
from typing import Tuple


async def convert_to_pdf(filename: str, file_bytes: bytes) -> Tuple[str, bytes]:
    """
    Converts a given file to PDF using the soffice command.

    Args:
        filename: The original filename (e.g., 'document.docx', 'image.jpg').
        file_bytes: The bytes content of the file to be converted.

    Returns:
        A tuple containing the PDF filename (e.g., 'document.pdf') and its bytes content.

    Raises:
        FileNotFoundError: If the 'soffice' command is not found.
        RuntimeError: If the conversion process fails.
    """
    # Create secure temporary directories and files
    with tempfile.TemporaryDirectory() as input_dir:
        input_filepath = os.path.join(input_dir, filename)
        with open(input_filepath, 'wb') as f:
            f.write(file_bytes)

        with tempfile.TemporaryDirectory() as output_dir:
            # Construct the soffice command
            # --headless: Run LibreOffice in headless mode (no GUI)
            # --convert-to pdf: Specify the conversion format
            # --outdir: Specify the output directory
            # The input file path
            command = [
                'soffice',
                '--headless',
                '--convert-to',
                'pdf',
                '--outdir',
                output_dir,
                input_filepath
            ]

            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    error_message = f"soffice conversion failed with error: {stderr.decode()}"
                    raise RuntimeError(error_message)

                # Determine the output PDF filename
                name_without_ext = os.path.splitext(filename)[0]
                pdf_filename = f"{name_without_ext}.pdf"
                pdf_filepath = os.path.join(output_dir, pdf_filename)

                if not os.path.exists(pdf_filepath):
                    raise RuntimeError(f"PDF file not found after conversion: {pdf_filepath}. soffice output: {stdout.decode()}")

                with open(pdf_filepath, 'rb') as f:
                    pdf_bytes = f.read()

                return pdf_filename, pdf_bytes

            except FileNotFoundError:
                raise FileNotFoundError("The 'soffice' command was not found. Please ensure LibreOffice is installed and 'soffice' is in your PATH.")
            except Exception as e:
                raise RuntimeError(f"An unexpected error occurred during conversion: {e}")
