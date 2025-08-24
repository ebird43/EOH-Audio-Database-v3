def main():
    print("Adidam EOH Index Importer")
    print("=========================")
    
    # Look for the file in the current directory first
    if os.path.exists("EOH Index.docx"):
        docx_path = "EOH Index.docx"
        print(f"Found EOH Index.docx in current directory")
    else:
        # Ask for document file
        docx_path = input("Enter path to EOH Index.docx file: ")
        # Remove quotes if present
        docx_path = docx_path.strip('"\'')
    
    # Import the data
    importer = EohIndexImporter()
    result = importer.import_from_docx(docx_path)
    
    if result:
        print("Import successful!")
    else:
        print("Import failed. Please check the file path and try again.")