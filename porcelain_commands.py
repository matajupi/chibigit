from pathlib import Path

from plumbing_commands import chibi_hash_object, chibi_update_index, chibi_write_tree, \
    get_managed_files, parse_head, chibi_commit_tree, chibi_update_ref


def chibi_snap():
    for path in get_managed_files():
        chibi_hash_object(path)

    chibi_update_index()


def chibi_commit(message):
    tree_hash = chibi_write_tree()
    head = parse_head()
    parent_hash = head["latest"] if "latest" in head else ""
    commit_hash = chibi_commit_tree(tree_hash, parent_hash, message)
    chibi_update_ref(commit_hash)


def chibi_init():
    chibi_path = Path.cwd() / ".chibi"
    if chibi_path.is_dir():
        print("Project file already exists.")
        exit(1)

    chibi_path.mkdir()

