import glob
from jgo.jgo import InvalidEndpoint
from jgo.jgo import jgo_parser, default_config, usage, epilog, resolve_dependencies, _jgo_main
import re
import os
import pathlib
import unittest
import shutil
import tempfile

import pytest

import logging

_logger = logging.getLogger(__name__)
_logger.level = logging.INFO

SJC_VERSION = "2.87.0"
SJC_OPTIONAL_VERSION = "1.0.0"
MANAGED_ENDPOINT = (
    "org.scijava:scijava-common:{}+org.scijava:scijava-optional:MANAGED".format(
        SJC_VERSION
    )
)
MANAGED_PRIMARY_ENDPOINT = "org.scijava:scijava-common:MANAGED"
REPOSITORIES = {"scijava.public": "https://maven.scijava.org/content/groups/public"}


def resolve_managed(endpoint, cache_dir, m2_repo):
    return resolve_dependencies(
        endpoint,
        m2_repo=m2_repo,
        cache_dir=cache_dir,
        manage_dependencies=True,
        repositories=REPOSITORIES,
    )

def find_jar_matching(jars, pattern):
    for jar in jars:
        lastindex = jar.rindex(os.sep)
        if jar[lastindex:].find(pattern) != -1:
            return jar
    return None


class ArgParserTest(unittest.TestCase):

    def test_arg_parser(self):
        parser = jgo_parser()
        argv = ["mvxcvi:cljstyle", "fix", "/c/Projects/py2many/tests/expected/demorgan.smt"]
        
        args = parser.parse_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "/c/Projects/py2many/tests/expected/demorgan.smt"])
        
    def test_arg_parser_windows_drive(self):
        parser = jgo_parser()
        argv = ["mvxcvi:cljstyle", "fix", "c:/Projects/py2many/tests/expected/demorgan.smt"]
        
        args = parser.parse_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "c:/Projects/py2many/tests/expected/demorgan.smt"])

    def test_arg_parser_windows_sep(self):
        parser = jgo_parser()
        argv = ["mvxcvi:cljstyle", "fix", "c:\\Projects\\py2many\\tests\\expected\\demorgan.smt"]
        
        args = parser.parse_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "c:\\Projects\\py2many\\tests\\expected\\demorgan.smt"])

def test_help(capsys):
    with pytest.raises(SystemExit):
        _jgo_main(["-h"])
    captured = capsys.readouterr()
    assert captured.out.startswith("usage: ")
    print(captured.out)
    assert False
    epilog_start = captured.out.find("Run Java main class from Maven coordinates")
    assert captured.out[len("usage: "):epilog_start].strip() == usage.strip()
    assert captured.err == ""

class FindEndpointTest: #(unittest.TestCase):

    def test_arg_parser(self):
        parser = jgo_parser()
        config = default_config()
        shortcuts = config["shortcuts"]

        argv = ["mvxcvi:cljstyle", "fix", "/c/Projects/py2many/tests/expected/demorgan.smt"]
        endpoint_index = find_endpoint(argv, shortcuts)
        self.assertEqual(endpoint_index, 0)
        args, unknown = parser.parse_known_args(argv[:endpoint_index])
        program_args = [] if endpoint_index == -1 else argv[endpoint_index + 1 :]
        self.assertEqual(program_args, ["fix", "/c/Projects/py2many/tests/expected/demorgan.smt"])
        endpoint_string = argv[endpoint_index]
        self.assertEqual(endpoint_string, "mvxcvi:cljstyle")

    def test_arg_parser_windows_drive(self):
        parser = jgo_parser()
        config = default_config()
        shortcuts = config["shortcuts"]

        argv = ["mvxcvi:cljstyle", "fix", "c:/Projects/py2many/tests/expected/demorgan.smt"]
        endpoint_index = find_endpoint(argv, shortcuts)
        self.assertEqual(endpoint_index, 0)
        args, unknown = parser.parse_known_args(argv[:endpoint_index])
        program_args = [] if endpoint_index == -1 else argv[endpoint_index + 1 :]
        self.assertEqual(program_args, ["fix", "c:/Projects/py2many/tests/expected/demorgan.smt"])
        endpoint_string = argv[endpoint_index]
        self.assertEqual(endpoint_string, "mvxcvi:cljstyle")

    def test_arg_parser_windows_sep(self):
        parser = jgo_parser()
        config = default_config()
        shortcuts = config["shortcuts"]

        argv = ["mvxcvi:cljstyle", "fix", "c:\\Projects\\py2many\\tests\\expected\\demorgan.smt"]
        endpoint_index = find_endpoint(argv, shortcuts)
        self.assertEqual(endpoint_index, 0)
        args, unknown = parser.parse_known_args(argv[:endpoint_index])
        program_args = [] if endpoint_index == -1 else argv[endpoint_index + 1 :]
        self.assertEqual(program_args, ["fix", "c:\\Projects\\py2many\\tests\\expected\\demorgan.smt"])
        endpoint_string = argv[endpoint_index]
        self.assertEqual(endpoint_string, "mvxcvi:cljstyle")


if __name__ == "__main__":
    unittest.main()
