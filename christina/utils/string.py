def get_extension(path: str) -> str:
    filename = path[path.rfind('/')+1:]
    ext = filename[filename.rfind('.')+1:]

    # means this file has no extension
    if ext == filename:
        ext = ''

    return ext
