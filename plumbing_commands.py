import sys
import hashlib
import zlib
import re

from pathlib import Path


def get_root_dir():
    cur_dir = Path.cwd()

    while True:
        entries = cur_dir.iterdir()
        if cur_dir / ".chibi" in entries:
            break

        if cur_dir == cur_dir.parent:
            print("Error: .chibi directory not found", file=sys.stderr)
            sys.exit(1)

        cur_dir = cur_dir.parent

    return cur_dir


def get_blob_content(file_path):
    with file_path.open("rb") as file:
        file_content = file.read()
    return f"blob {len(file_content)}\0".encode() + file_content


def write_object(obj_content):
    compressed = zlib.compress(obj_content)

    obj_hash = hashlib.sha1(obj_content).hexdigest()
    dir_name, file_name = obj_hash[:2], obj_hash[2:]

    obj_dir = get_root_dir() / ".chibi" / "objects" / dir_name
    obj_dir.mkdir(parents=True, exist_ok=True)

    obj_path = obj_dir / file_name
    with obj_path.open("wb") as file:
        file.write(compressed)

    return obj_hash


def chibi_hash_object(file_path):
    blob_content = get_blob_content(file_path)
    write_object(blob_content)


def get_managed_files():
    ignore_patterns = [r"/\.chibi/"]

    root_dir = get_root_dir()
    chibiignore_path = root_dir / ".chibiignore"
    if chibiignore_path.is_file():
        with chibiignore_path.open('r') as file:
            for line in file:
                pattern = line.strip()
                if pattern:
                    ignore_patterns.append(pattern)

    managed_files = []
    for entry_path in root_dir.glob("**/*"):
        if not entry_path.is_file():
            continue
        for pattern in ignore_patterns:
            if re.search(pattern, str(entry_path)):
                break
        else:
            managed_files.append(entry_path)

    return managed_files


def calc_padding(file_path_size):
    entry_size = 4 + 20 + 2 + file_path_size
    return 8 - entry_size % 8


# Index format
# ヘッダー
# - 32bits    Index header
# - 32bits    Index version
# - 32bits    エントリー数
# エントリー
# - 32bits    パーミッション(mode)
# - 160bits   blobのハッシュ(4bits * 40文字)
# - 16bits    ファイルパスサイズ
# - ??bytes   ファイルパス
# - 1-8bytes  パディング
def chibi_update_index():
    file_paths = get_managed_files()
    index_path = get_root_dir() / ".chibi" / "index"

    index_content = bytearray()
    index_content.extend(b"DIRC")
    index_content.extend((1).to_bytes(4, "big"))
    index_content.extend(len(file_paths).to_bytes(4, "big"))

    for file_path in file_paths:
        mode = file_path.stat().st_mode

        blob_content = get_blob_content(file_path)
        blob_hash = hashlib.sha1(blob_content).digest()

        file_path_raw = str(file_path).encode()
        file_path_size = len(file_path_raw)
        padding = calc_padding(file_path_size)

        index_content.extend(mode.to_bytes(4, "big"))
        index_content.extend(blob_hash)
        index_content.extend(file_path_size.to_bytes(2, "big"))
        index_content.extend(file_path_raw)
        for _ in range(padding):
            index_content.extend(b'\0')

    index_content = bytes(index_content)

    with index_path.open('wb') as file:
        file.write(index_content)


def parse_index():
    entries = []
    try:
        index_path = get_root_dir() / ".chibi" / "index"
        assert(index_path.is_file())

        with index_path.open("rb") as file:
            index_content = file.read()

        assert(index_content[:4].decode() == "DIRC")
        assert(int.from_bytes(index_content[4:8], "big") == 1)
        n_entries = int.from_bytes(index_content[8:12], "big")

        offset = 12
        for _ in range(n_entries):
            mode = int.from_bytes(index_content[offset:offset + 4], "big")
            offset += 4
            blob_hash = index_content[offset:offset + 20].hex()
            offset += 20
            file_path_size = int.from_bytes(index_content[offset:offset + 2], "big")
            offset += 2
            file_path = index_content[offset:offset + file_path_size].decode()
            offset += file_path_size

            padding = calc_padding(file_path_size)
            offset += padding

            entries.append({"mode": mode, "blob_hash": blob_hash, "file_path": file_path})
    except:
        print("Error: Failed to parse index", file=sys.stderr)
        sys.exit(1)

    return entries


def chibi_ls_files():
    entries = parse_index()
    for entry in entries:
        print(f"{entry['mode']:0>6o} {entry['blob_hash']}\t{entry['file_path']}")


def create_tree(path, entries):
    entry = entries[path]
    entries_content = bytearray()
    for child_path in entry["childs"]:
        child = entries[child_path]
        entries_content.extend(f"{child['mode']:0>6o} {child_path}\0".encode())
        entries_content.extend(bytes.fromhex(child["hash"]))
    entries_content = bytes(entries_content)

    tree_content = bytearray()
    tree_content.extend(f"tree {len(entries_content)}\0".encode())
    tree_content.extend(entries_content)
    tree_content = bytes(tree_content)

    tree_hash = write_object(tree_content)
    return tree_hash


def create_tree_rec(path, entries):
    entry = entries[path]
    if entry["type"] == "file":
        return

    for child_path in entry["childs"]:
        create_tree_rec(child_path, entries)

    tree_hash = create_tree(path, entries)
    entry["hash"] = tree_hash


def chibi_write_tree():
    root_dir = get_root_dir()

    files = parse_index()
    entries = {}
    for file in files:
        path = Path(file["file_path"])
        entries[path] = {"type": "file", "mode": file["mode"], "hash": file["blob_hash"]}

        while True:
            if path.parent == path:
                print(f"Error: Unmanaged file: {path}", file=sys.stderr)
                sys.exit(1)

            if path.parent not in entries:
                entries[path.parent] = {"type": "dir", "childs": [], "mode": 16384, "hash": None}

            if path not in entries[path.parent]["childs"]:
                entries[path.parent]["childs"].append(path)

            if path.parent == root_dir:
                break

            path = path.parent

    create_tree_rec(root_dir, entries)

    return entries[root_dir]["hash"]


def parse_head():
    head_path = get_root_dir() / ".chibi" / "HEAD"

    hashes = {}
    if not head_path.is_file():
        return hashes

    try:
        with head_path.open('r') as file:
            for line in file:
                key, value = list(map(lambda s: s.strip(), line.split(':')))
                hashes[key] = value
    except:
        print("Error: Failed to parse HEAD", file=sys.stderr)
        sys.exit(1)

    return hashes


def chibi_commit_tree(tree_hash, parent_hash, message):
    body_content = bytearray()
    body_content.extend(f"tree {tree_hash}\n".encode())
    if parent_hash:
        body_content.extend(f"parent {parent_hash}\n".encode())
    body_content.extend(b"\n")
    body_content.extend(f"{message}\n".encode())
    body_content = bytes(body_content)

    commit_content = bytearray()
    commit_content.extend(f"commit {len(body_content)}\0".encode())
    commit_content.extend(body_content)
    commit_content = bytes(commit_content)

    commit_hash = write_object(commit_content)
    return commit_hash


def chibi_update_ref(commit_hash):
    head_path = get_root_dir() / ".chibi" / "HEAD"
    with head_path.open('w') as file:
        file.write(f"latest: {commit_hash}\n")
        file.write(f"current: {commit_hash}\n")

