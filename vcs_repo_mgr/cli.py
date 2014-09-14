# Command line interface for vcs-repo-mgr.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: September 14, 2014
# URL: https://github.com/xolox/python-vcs-repo-mgr

"""
Usage: vcs-tool [OPTIONS] [ARGS]

Command line program to perform common operations (in the context of
packaging/deployment) on version control repositories. Supports Bazaar,
Mercurial and Git repositories.

Supported options:

  -r, --repository=REPOSITORY_NAME

    Select a repository to operate on by providing the name of a repository
    defined in one of the configuration files ~/.vcs-repo-mgr.ini and
    /etc/vcs-repo-mgr.ini.

  --rev, --revision=REVISION

    Select a revision to operate on. Accepts any string that's supported by the
    VCS system that manages the repository, which means you can provide branch
    names, tag names, exact revision ids, etc. This option is used in
    combination with the --find-revision-number, --find-revision-id and
    --export options.

    If this option is not provided a default revision is selected: `last:1' for
    Bazaar repositories, `master' for git repositories and `default' (not
    `tip'!) for Mercurial repositories.

  -n, --find-revision-number

    Print the local revision number (an integer) of the revision given with the
    --revision option. Revision numbers are useful as a build number or when a
    simple, incrementing version number is required. Revision numbers should
    not be used to unambiguously refer to a revision (use revision ids for that
    instead). This option is used in combination with the --repository and
    --revision options.

  -i, --find-revision-id

    Print the global revision id (a string) of the revision given with the
    --revision option. Global revision ids are useful to unambiguously refer to
    a revision. This option is used in combination with the --repository and
    --revision options.

  -s, --sum-revisions

    Print the summed revision numbers of multiple repository/revision pairs.
    The repository/revision pairs are taken from the positional arguments to
    vcs-repo-mgr.

    This is useful when you're building a package based on revisions from
    multiple VCS repositories. By taking changes in all repositories into
    account when generating version numbers you can make sure that your version
    number is bumped with every single change.

  -u, --update

    Create/update the local clone of a remote repository by pulling the latest
    changes from the remote repository. This option is used in combination with
    the --repository option.

  -e, --export=DIRECTORY

    Export the contents of a specific revision of a repository to a local
    directory. This option is used in combination with the --repository and
    --revision options.

  -d, --find-directory

    Print the absolute pathname of a local repository. This option is used in
    combination with the --repository option.

  -v, --verbose

    Make more noise.

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import functools
import getopt
import logging
import os
import sys

# External dependencies.
import coloredlogs
from executor import execute

# Modules included in our package.
from vcs_repo_mgr import find_configured_repository, sum_revision_numbers

# Initialize a logger.
logger = logging.getLogger(__name__)

# Inject our logger into all execute() calls.
execute = functools.partial(execute, logger=logger)

def main():
    """
    The command line interface of the ``vcs-tool`` command.
    """
    # Initialize logging to the terminal.
    coloredlogs.install()
    # Command line option defaults.
    repository = None
    revision = None
    actions = []
    # Parse the command line arguments.
    try:
        options, arguments = getopt.gnu_getopt(sys.argv[1:], 'r:dnisue:vh', [
            'repository=', 'rev=', 'revision=', 'find-directory',
            'find-revision-number', 'find-revision-id', 'sum-revisions',
            'update', 'export=', 'verbose', 'help'
        ])
        for option, value in options:
            if option in ('-r', '--repository'):
                name = value.strip()
                assert name, "Please specify the name of a repository! (using -r, --repository)"
                repository = find_configured_repository(name)
            elif option in ('--rev', '--revision'):
                revision = value.strip()
                assert revision, "Please specify a nonempty revision string!"
            elif option in ('-d', '--find-directory'):
                assert repository, "Please specify a repository first!"
                actions.append(functools.partial(print_directory, repository))
            elif option in ('-n', '--find-revision-number'):
                assert repository, "Please specify a repository first!"
                actions.append(functools.partial(print_revision_number, repository, revision))
            elif option in ('-i', '--find-revision-id'):
                assert repository, "Please specify a repository first!"
                actions.append(functools.partial(print_revision_id, repository, revision))
            elif option in ('-s', '--sum-revisions'):
                assert len(arguments) >= 2, "Please specify one or more repository/revision pairs!"
                actions.append(functools.partial(print_summed_revisions, arguments))
                arguments = []
            elif option in ('-u', '--update'):
                assert repository, "Please specify a repository first!"
                actions.append(functools.partial(repository.update))
            elif option in ('-e', '--export'):
                directory = value.strip()
                assert repository, "Please specify a repository first!"
                assert directory, "Please specify the directory where the revision should be exported!"
                actions.append(functools.partial(repository.export, directory, revision))
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-h', '--help'):
                usage()
                return
        if not actions:
            usage()
            return
    except Exception as e:
        logger.error(e)
        print('')
        usage()
        sys.exit(1)
    # Execute the requested action(s).
    try:
        for action in actions:
            action()
    except Exception:
        logger.exception("Failed to execute requested action(s)!")
        sys.exit(1)

def print_directory(repository):
    print(repository.local)

def print_revision_number(repository, revision):
    print(repository.find_revision_number(revision))

def print_revision_id(repository, revision):
    print(repository.find_revision_id(revision))

def print_summed_revisions(arguments):
    print(sum_revision_numbers(arguments))

def usage():
    print(__doc__.strip())

# vim: ts=4 sw=4 et
