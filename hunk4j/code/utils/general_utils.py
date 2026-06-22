def read_file_content(file_path):
    """
    Read the content of a file. Try UTF-8 encoding first, falling back to ISO-8859-1.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='ISO-8859-1') as f:
            return f.read()
