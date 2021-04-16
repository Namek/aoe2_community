def copy_file(source_file, dest_file, chunk_size=2 ** 16):
    source_file.seek(0)
    read, write, offset = source_file.read, dest_file.write, source_file.tell()
    while 1:
        buf = read(chunk_size)
        if not buf: break
        write(buf)
    source_file.seek(offset)
