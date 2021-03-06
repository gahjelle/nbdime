#!/usr/bin/env python
"""A git diff driver for notebooks.

Uses nbdime to create diffs for notebooks instead of plain text diffs of JSON.
Note that this requires the following to be set in .gitattributes to correctly
identify filetypes with the driver:

    *.ipynb     diff=jupyternotebook

Enable in your global git config with:

    git-nbdiffdriver config --enable [--global]

Use with:

    git diff [<commit> [<commit>]]
"""

from __future__ import print_function

import os
import sys
from subprocess import check_call, check_output, CalledProcessError

from . import nbdiffapp


def enable(global_=False):
    """Enable nbdime git diff driver"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')

    check_call(cmd + ['diff.jupyternotebook.command', 'git-nbdiffdriver diff'])
    if global_:
        try:
            bpath = check_output(['git', 'config', '--global', 'core.attributesfile'])
            gitattributes = os.path.expanduser(bpath.decode('utf8', 'replace').strip())
        except CalledProcessError:
            gitattributes = os.path.expanduser('~/.gitattributes')
    else:
        # find .gitattributes in current dir
        path = os.path.abspath('.')
        if not os.path.exists(os.path.join(path, '.git')):
            print("No .git directory in %s, skipping git attributes" % path, file=sys.stderr)
            return
        gitattributes = os.path.join(path, '.gitattributes')

    if os.path.exists(gitattributes):
        with open(gitattributes) as f:
            if 'diff=jupyternotebook' in f.read():
                # already written, nothing to do
                return

    with open(gitattributes, 'a') as f:
        f.write('\n*.ipynb\tdiff=jupyternotebook\n')


def disable(global_=False):
    """Disable nbdime git diff drivers"""
    cmd = ['git', 'config']
    if global_:
        cmd.append('--global')
    try:
        check_call(cmd + ['--remove-section', 'diff.jupyternotebook'])
    except CalledProcessError:
        # already unset
        pass


def show_diff(before, after):
    """Run the diff
    """
    # TODO: handle /dev/null (Windows equivalent?) for new or deleted files
    nbdiffapp.main([before, after])


def main():
    import argparse
    parser = argparse.ArgumentParser('git-nbdiffdriver', description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='subcommand')

    diff_parser = subparsers.add_parser('diff',
        description="The actual entrypoint for the diff tool. Git will call this."
    )
    # Argument list
    # path old-file old-hex old-mode new-file new-hex new-mode [ rename-to ]
    diff_parser.add_argument('path')
    diff_parser.add_argument('a', nargs='?', default=None)
    diff_parser.add_argument('a_sha1', nargs='?', default=None)
    diff_parser.add_argument('a_mode', nargs='?', default=None)
    diff_parser.add_argument('b', nargs='?', default=None)
    diff_parser.add_argument('b_sha1', nargs='?', default=None)
    diff_parser.add_argument('b_mode', nargs='?', default=None)
    diff_parser.add_argument('rename_to', nargs='?', default=None)

    # TODO: From git docs: "For a path that is unmerged, GIT_EXTERNAL_DIFF is called with 1 parameter, <path>."

    config = subparsers.add_parser('config',
        description="Configure git to use nbdime for notebooks in `git diff`")
    config.add_argument('--global', action='store_true', dest='global_',
        help="configure your global git config instead of the current repo"
    )
    enable_disable = config.add_mutually_exclusive_group(required=True)
    enable_disable.add_argument('--enable', action='store_const',
        dest='config_func', const=enable,
        help="enable nbdime diff driver via git config"
    )
    enable_disable.add_argument('--disable', action='store_const',
        dest='config_func', const=disable,
        help="disable nbdime diff driver via git config"
    )
    opts = parser.parse_args()
    if opts.subcommand == 'diff':
        show_diff(opts.a, opts.b)
    elif opts.subcommand == 'config':
        opts.config_func(opts.global_)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
