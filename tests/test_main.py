import unittest

from jgo.jgo import jgo_parser


class ArgParserTest(unittest.TestCase):

    def test_program_arg_path(self):
        parser = jgo_parser()
        argv = ["mvxcvi:cljstyle", "fix", "/c/path/to/file.clj"]
        
        args = parser.parse_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "/c/path/to/file.clj"])
        
    def test_program_arg_path_windows_drive(self):
        parser = jgo_parser()
        argv = ["mvxcvi:cljstyle", "fix", "c:/path/to/file.clj"]
        
        args = parser.parse_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "c:/path/to/file.clj"])

    def test_program_arg_path_windows_sep(self):
        parser = jgo_parser()
        argv = ["mvxcvi:cljstyle", "fix", "c:\\path\\to\\file.clj"]
        
        args = parser.parse_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "c:\\path\\to\\file.clj"])

    def test_jvm_args(self):
        parser = jgo_parser()
        argv = ["-Xms1G", "mvxcvi:cljstyle", "fix", "c:\\path\\to\\file.clj"]
        
        args, unknown = parser.parse_known_args(argv)
        self.assertEqual(args.endpoint, "mvxcvi:cljstyle")
        self.assertEqual(args.program_args, ["fix", "c:\\path\\to\\file.clj"])
        self.assertEqual(unknown, ["-Xms1G"])


if __name__ == "__main__":
    unittest.main()
