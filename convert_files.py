import os
import shutil
import pathlib
from PIL import Image # For saving images

from parsestudio.parse import PDFParser

def main():
    """
    Main function to process files.
    Monitors the 'input' directory for PDF files, processes them,
    and moves them to 'input/processed'.
    """
    input_dir = "input"
    output_dir = "output" # Define the base output directory
    processed_dir = os.path.join(input_dir, "processed")

    # Create the 'processed' and base 'output' subdirectories if they don't exist
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Scanning for PDF files in '{input_dir}' (excluding '{processed_dir}')...")

    pdf_files_to_process = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            source_path = os.path.join(input_dir, filename)
            # Ensure it's a file and not a directory (though listdir items are usually files/dirs, not full paths)
            # and importantly, that it's not already in the processed directory (which os.listdir on input_dir alone won't filter)
            if os.path.isfile(source_path): # This check implicitly handles not picking up 'processed' if it were a .pdf file
                pdf_files_to_process.append(source_path)

    if not pdf_files_to_process:
        print("No new PDF files found to process.")
    else:
        print("Found the following PDF files to process:")
        for pdf_file in pdf_files_to_process:
            print(f"Processing {pdf_file}...")
            parser = PDFParser()
            processed_successfully = False # Flag to track if processing and saving are successful

            try:
                parsed_outputs = parser.run(pdf_path=pdf_file, modalities=["text", "tables", "images"])

                if not parsed_outputs:
                    print(f"  No output generated for {pdf_file}.")
                    # Even if no output, we might consider it "processed" if no error, to avoid reprocessing.
                    # However, if nothing to save, moving it might be debatable. For now, let's only move if content was saved.
                else:
                    # Create a subdirectory in 'output' for this PDF's content
                    pdf_basename = pathlib.Path(pdf_file).stem
                    current_output_subdir = os.path.join(output_dir, pdf_basename)
                    os.makedirs(current_output_subdir, exist_ok=True)
                    print(f"  Saving extracted content to '{current_output_subdir}'")

                    # Assuming one Document object per PDF file for simplicity here
                    # If a single PDF can result in multiple Document objects, this logic might need adjustment
                    # or save them in the same subdir with indexed names. For now, take the first.
                    output_doc = parsed_outputs[0] 

                    # Save text content
                    if output_doc.text:
                        text_file_path = os.path.join(current_output_subdir, "text_content.txt")
                        with open(text_file_path, "w", encoding="utf-8") as f:
                            # Ensure we are writing a string. output_doc.text might be a TextElement object.
                            f.write(str(output_doc.text)) 
                        print(f"    Saved text to '{text_file_path}'")

                    # Save tables
                    if output_doc.tables:
                        for idx, table in enumerate(output_doc.tables):
                            table_file_path = os.path.join(current_output_subdir, f"table_{idx+1}.md")
                            # Assuming table.markdown contains the markdown string
                            with open(table_file_path, "w", encoding="utf-8") as f:
                                f.write(table.markdown) # Or table.to_markdown() if it's an object with a method
                            print(f"    Saved table {idx+1} to '{table_file_path}'")
                    
                    # Save images
                    if output_doc.images:
                        for idx, img_obj in enumerate(output_doc.images):
                            # Assuming img_obj.image is a PIL Image object
                            # and img_obj.name or a similar attribute might give a preferred name/extension
                            # For now, save as PNG.
                            img_file_path = os.path.join(current_output_subdir, f"image_{idx+1}.png")
                            img_obj.image.save(img_file_path) # PIL Image's save method
                            print(f"    Saved image {idx+1} to '{img_file_path}'")
                    
                    processed_successfully = True # Mark as successful if we got here

            except Exception as e:
                print(f"    Error during processing or saving for {pdf_file}: {e}")
                processed_successfully = False

            # Move the processed file to the 'input/processed' directory if all went well
            if processed_successfully:
                destination_path = os.path.join(processed_dir, os.path.basename(pdf_file))
                try:
                    shutil.move(pdf_file, destination_path)
                    print(f"  Successfully processed and moved '{pdf_file}' to '{destination_path}'")
                except Exception as e:
                    print(f"    Error moving {pdf_file} to {destination_path}: {e}")
            else:
                print(f"  File '{pdf_file}' was not moved due to processing/saving errors or no content.")


if __name__ == "__main__":
    main()
