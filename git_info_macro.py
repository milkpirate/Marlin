#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract git info from current repo. It will be written to stderr/stdout as C
build arguments. Optionally a C headerfile or a JSON file with the info can be
written.

Usage:
  git_info.py [--header=<h_file>] [--json=<json_file>]
  git_info.py -h | --help
  git_info.py --version

Options:
  -j --json=<json_file>     Path to write the JSON file to.
  -H --header=<h_file>      Path to write the C header file to.
  -h --help                 Show this screen.
  --version                 Show version.
"""

from __future__ import print_function

import docopt
import git
import json
import shlex
import sys
import time

from pprint import pprint as pp


version_file_h_path = './Marlin/repo_info.h'
version_file_json_path = './repo_info.json'


def main(argv):
    args = docopt.docopt(
        __doc__,
        argv=argv[1:],
        help='0.1',
        version=None,
        options_first=True
    )
    #print(args); exit(0)

    repo = git.Repo('.')

    git_info = dict(
        commit_hash=repo.head.commit.hexsha,
        commit_hash_short=repo.head.commit.hexsha[:8],
        branch=repo.active_branch.name,
        author=repo.head.commit.author.name,
        authored_date=format_time(repo.head.commit.authored_date),
        build_date=format_time(time.time()),
        commit_msg=repo.head.commit.message,
    )

    if args['--json']:
        with open(args['--json'], 'w') as vf:
            content = str_dict_values(git_info)
            content = json.dumps(
                content,
                sort_keys=True,
                indent=2,
            )
            vf.write(content)

    git_info = repr_dict_values(git_info)
    git_info = prefix_dict_keys('git_', git_info)

    commit_hash = git_info['git_commit_hash']
    hash_info = get_hash_arg_pairs(commit_hash)
    hash_info = repr_dict_values(hash_info)

    version_file = gen_version_file_lines(upper_dict_keys(git_info))
    version_file += gen_version_file_lines(hash_info)
    version_file = '\n'.join(version_file)
    version_file = '#pragma once\n' + version_file

    if args['--header']:
        with open(args['--header'], 'w') as vf:
            vf.write(version_file)

    build_args = gen_build_args_from_dict(git_info)
    build_args += ' '
    build_args += gen_build_args_from_dict(hash_info)

    print(build_args)
    for line in shlex.split(build_args):
        eprint(line)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def gen_version_file_lines(dct):
    """
    Generate version file lines from dct. Dictionary has to habe both, \
keys and values to be ``str``.

    :param dct: Dictionary with ``str`` key/values.
    :type dct: dict

    :retrun: Versionfile lines
    :rtype: list of str

    :raises: TypeError

    >>> gen_version_file_lines(dict(a="abc", b='def'))
    ['#define a "abc"', '#define b "def"']
    >>> gen_version_file_lines({123: "abc"})
    Traceback (most recent call last):
        ...
    TypeError: not all keys of the dict are of type str
    >>> gen_version_file_lines({"abc": 123})
    Traceback (most recent call last):
        ...
    TypeError: not all values of the dict are of type str
    """

    if not all(isinstance(key, str) for key in dct.keys()):
        raise TypeError("not all keys of the dict are of type str")
    if not all(isinstance(val, str) for val in dct.values()):
        raise TypeError("not all values of the dict are of type str")

    lines = []
    for k, v in dct.items():
        lines.append('#define {k} "{v}"'.format(k=k, v=v))

    return lines


def upper_dict_keys(dct):
    """
    Apply ``.upper()`` in all dict keys. All keys must be of type ``str``.

    :param dct: Dictionary to upper keys.
    :type dct: dict

    :retrun: The dct with uppered keys.
    :rtype: dict

    :raises: TypeError

    >>> upper_dict_keys(dict(a="abc", b='def'))
    {'A': 'abc', 'B': 'def'}
    >>> upper_dict_keys('no dict')
    Traceback (most recent call last):
        ...
    TypeError: dct is not of type dict
    >>> upper_dict_keys({'abc': 'def', 123: 'jkl'})
    Traceback (most recent call last):
        ...
    TypeError: not all keys of the dict are of type str
    """

    if not isinstance(dct, dict):
        raise TypeError("dct is not of type dict")
    if not all(isinstance(key, str) for key in dct.keys()):
        raise TypeError("not all keys of the dict are of type str")

    new_dct = dict()
    for k, v in dct.items():
        new_dct[k.upper()] = v

    return new_dct


def str_dict_values(dct):
    """
    Converts all values of a dict to type ``str`` via de/en-coding.

    :param dct: Dictionary to stringify values.
    :type dct: dict

    :retrun: The same dct with stringified values.
    :rtype: dict ``str`` values

    :raises: TypeError

    >>> str_dict_values(dict(a=123, b=u'abc', c='def')) == {'a': '123', 'b': 'abc', 'c': 'def'}
    True
    >>> str_dict_values(123)
    Traceback (most recent call last):
        ...
    TypeError: dct is not of type dict
    """

    if not isinstance(dct, dict):
        raise TypeError("dct is not of type dict")
    if not all(isinstance(key, str) for key in dct.keys()):
        raise TypeError("not all keys of the dict are of type str")

    new_dict = dict()
    for k, v in dct.items():
        if type(v).__name__ == 'bytes':
            v = v.decode('utf-8')
        elif type(v).__name__ == 'unicode':
            v = v.encode('utf-8')

        dct[k] = str(v)

    return dct


def repr_dict_values(dct):
    """
    Converts all values of a dict to type ``str`` via de/en-coding and \
``.repr()``.

    :param dct: Dictionary to stringify values.
    :type dct: dict

    :retrun: The same dct with stringified values.
    :rtype: dict ``str`` values

    :raises: TypeError

    >>> repr_dict_values(dict(a=123, b=u'abc\\n', c='def')) == {'a': '123', 'b': 'abc\\\\n', 'c': 'def'}
    True
    >>> repr_dict_values(123)
    Traceback (most recent call last):
        ...
    TypeError: dct is not of type dict
    """

    if not isinstance(dct, dict):
        raise TypeError("dct is not of type dict")
    if not all(isinstance(key, str) for key in dct.keys()):
        raise TypeError("not all keys of the dict are of type str")

    new_dict = str_dict_values(dct)
    for k, v in dct.items():
        dct[k] = v.__repr__().replace("'", "")

    return dct


def prefix_dict_keys(pfx, dct):
    """
    Adds ``pfx`` to the keys of a dict where keys are ``str``.

    :param pfx: Prefix to adds
    :type pfx: ``str``

    :param dct: Dictionary with key/values
    :type dct: dict with ``str`` keys and ``str`` values

    :retrun: Dictionary with added prefix to keys.
    :rtype: dict with ``str`` keys

    :raises: TypeError

    >>> prefix_dict_keys('ABC_', dict(a=1, b=2)) == {'ABC_a': 1, 'ABC_b': 2}
    True
    >>> prefix_dict_keys(123, dict())
    Traceback (most recent call last):
        ...
    TypeError: prefix is not of type str
    >>> prefix_dict_keys("pfx", 123)
    Traceback (most recent call last):
        ...
    TypeError: dct is not of type dict
    >>> prefix_dict_keys("pfx", {"abc": 123, 123: 123})
    Traceback (most recent call last):
        ...
    TypeError: not all keys of the dict are of type str
    """

    if not isinstance(pfx, str):
        raise TypeError("prefix is not of type str")
    if not isinstance(dct, dict):
        raise TypeError("dct is not of type dict")
    if not all(isinstance(key, str) for key in dct  .keys()):
        raise TypeError("not all keys of the dict are of type str")

    new_dict = dict()
    for k, v in dct.items():
        k = "{pfx}{k}".format(pfx=pfx, k=k)
        new_dict[k] = v

    return new_dict


def gen_build_args_from_dict(dct):
    """
    Turn a flat dict into build args. The args will have the following form \
``-D<key.upper()>='<value>'``. Both, keys and values of the dict, must be \
of type ``str``.

    :param dct: Ditionary with key/values
    :type dct: dict with ``str`` keys and ``str`` values

    :return: Build arguments string.
    :rtype: ``str``

    >>> gen_build_args_from_dict(dict(abc="def", ghi="jkl"))
    "-DABC='def' -DGHI='jkl'"
    >>> gen_build_args_from_dict({"str": "anotherstr", 123: "str"})
    Traceback (most recent call last):
        ...
    TypeError: not all keys of the dict are of type str
    >>> gen_build_args_from_dict({"str": "str", "anotherstr": 123})
    Traceback (most recent call last):
        ...
    TypeError: not all values of the dict are of type str
    """

    if not all(isinstance(key, str) for key in dct.keys()):
        raise TypeError("not all keys of the dict are of type str")
    if not all(isinstance(val, str) for val in dct.values()):
        raise TypeError("not all values of the dict are of type str")

    build_arg_parts = ["-D{name}={value!r}".format(
        name=name.upper(),
        value=value,
    ) for name, value in dct.items()]

    return ' '.join(build_arg_parts)


def get_hash_arg_pairs(hash):
    """
    Retunrs a dict with variables names as keys and hash parts as values.

    :param hash: Commit hash.
    :type hash: str

    :return: Dictionary with hash parts.
    :rtype: flat dict of str keys and str values

    :raises: TypeError, ValueError

    >>> get_hash_arg_pairs('abcdefghij') == {'GIT_COMMIT_HASH_8_DIGITS': 'abcdefgh', 'GIT_COMMIT_HASH_9_DIGITS': 'abcdefghi', 'GIT_COMMIT_HASH_10_DIGITS': 'abcdefghij'}
    True
    """

    hash_parts = list(string_to_part_list(hash))
    hash_pairs = dict()

    for hast_part in hash_parts:
        key = "GIT_COMMIT_HASH_{length}_DIGITS".format(length=len(hast_part))
        hash_pairs[key] = hast_part

    return hash_pairs


def string_to_part_list(string):
    """
    Returns longer getting parts of the begin of a string which is at least 8 \
letters long.

    :param string: String to get starts from.
    :type string: str

    :returns: List with longer and longer starts till full string
    :rtype: list of str

    :raises: TypeError, ValueError

    >>> for i in string_to_part_list("abcdefghij"): print(i)
    abcdefgh
    abcdefghi
    abcdefghij
    >>> next(string_to_part_list(123))
    Traceback (most recent call last):
        ...
    TypeError: no str given
    >>> next(string_to_part_list("2short"))
    Traceback (most recent call last):
        ...
    ValueError: string not long enought
    """
    min_length = 8

    if not isinstance(string, str):
        raise TypeError("no str given")
    if len(string) < min_length:
        raise ValueError("string not long enought")

    for idx in range(min_length, len(string)+1):
        yield string[:idx]


def format_time(date, frm="%d.%m.%Y %H:%M:%S"):
    """
    Format a float to the given strftime.

    :param date: Float of seconds since epoche
    :type date: Float

    :prarm frm: Format string to format to (default: "%a, %d.%m.%Y %H:%M:%S")
    :type frm: str

    >>> format_time(1570277370.8005953)
    '05.10.2019 12:09:30'
    >>> format_time(1570277370.8005953, "%a %H:%M:%S")
    'Sat 12:09:30'
    """
    return time.strftime(frm, time.gmtime(date))


if __name__ == '__main__':
    main(argv=sys.argv)
