import argparse


def create_parser_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Reddit month top parser')
    parser.add_argument('-p', '--posts', type=int, default=100, metavar='POSTS',
                        help='an integer for number of posts to be parsed (default: 100)')
    parser.add_argument('-o', '--offset', type=int, default=0, metavar='OFFSET',
                        help='an integer for posts offset (default: 0)')
    parser.add_argument('-w', '--workers', type=int, default=1, metavar='WORKERS',
                        help='sets a number of posts parsed in the same moment (default: 1)')
    return parser


def create_server_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Server for reddit month top parser to store parsed data')
    parser.add_argument('-d', '--database', type=str, default='mongo', choices=['mongo', 'postgres', 'file'],
                        help='which database you want to use (default: mongodb)')
    return parser
