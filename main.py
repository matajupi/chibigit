#!/usr/bin/env python3

import sys
import argparse

from pathlib import Path

from porcelain_commands import chibi_snap, chibi_commit, chibi_init
from plumbing_commands import chibi_ls_files, chibi_hash_object, chibi_update_index, \
    chibi_write_tree, chibi_commit_tree, chibi_update_ref


parser = argparse.ArgumentParser(description="Original git")
subparsers = parser.add_subparsers()

parser_snap = subparsers.add_parser("snap", help="Snapshot latest working directory")
parser_snap.set_defaults(handler=lambda _: chibi_snap())

parser_ls_files = subparsers.add_parser("ls-files", help="List index content")
parser_ls_files.set_defaults(handler=lambda _: chibi_ls_files())

parser_hash_object = subparsers.add_parser("hash-object", help="Make blob object")
parser_hash_object.add_argument("file")
parser_hash_object.set_defaults(handler=lambda args: chibi_hash_object(Path(args.file)))

parser_update_index = subparsers.add_parser("update-index", help="Update index content")
parser_update_index.set_defaults(handler=lambda _: chibi_update_index())

parser_write_tree = subparsers.add_parser("write-tree", help="Update tree")
parser_write_tree.set_defaults(handler=lambda _: chibi_write_tree())

parser_commit_tree = subparsers.add_parser("commit-tree", help="Commit tree")
parser_commit_tree.add_argument("tree_hash")
parser_commit_tree.add_argument("-m", "--message", default="")
parser_commit_tree.add_argument("-p", "--parent", default="")
parser_commit_tree.set_defaults(
    handler=lambda args: chibi_commit_tree(args.tree_hash, args.parent, args.message)
)

parser_update_ref = subparsers.add_parser("update-ref", help="Update reference")
parser_update_ref.add_argument("commit_hash")
parser_update_ref.set_defaults(handler=lambda args: chibi_update_ref(args.commit_hash))

parser_init = subparsers.add_parser("init", help="Init project")
parser_init.set_defaults(handler=lambda _: chibi_init())

parser_commit = subparsers.add_parser("commit", help="Register snapshot in local repository")
parser_commit.add_argument("-m", "--message", default="")
parser_commit.set_defaults(handler=lambda args: chibi_commit(args.message))


if __name__ == "__main__":
    args = parser.parse_args()
    if hasattr(args, "handler"):
        try:
            args.handler(args)
        except:
            print("Fatal error", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

