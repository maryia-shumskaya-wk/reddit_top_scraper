from post_parser import run_parser, create_parser_arg_parser


if __name__ == '__main__':
    arg_parser = create_parser_arg_parser()
    args = arg_parser.parse_args()

    run_parser(args.posts, args.offset, args.workers)
