from post_parser import run_server, create_server_arg_parser


if __name__ == '__main__':
    arg_parser = create_server_arg_parser()
    args = arg_parser.parse_args()
    run_server(args.database)
