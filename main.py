import argparse
from imap import IMAP

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='IMAP client')
    parser.add_argument("--ssl", action='store_true',
                        help="разрешить использование ssl, если сервер поддерживает (по умолчанию не использовать)")
    parser.add_argument("-s", "--server", type=str, required=True,
                        help="адрес (или доменное имя) IMAP-сервера в формате адрес[:порт] (порт по умолчанию 143).")
    parser.add_argument('-n', type=int, nargs='+', default=[], help='диапазон писем, по умолчанию все.')
    parser.add_argument("-u", "--user", type=str, default="",
                        help="имя пользователя, пароль спросить после запуска и не отображать на экране.")
    args = parser.parse_args()

    if len(args.n) > 2:
        print('Mail indices parameter takes 1 or 2 parameters')
        print(parser.print_help())
        exit(2)

    host_port = args.server.split(':')
    server = host_port[0]
    if len(host_port) == 2:
        port = host_port[1]
    else:
        port = 143
    server_Imap = IMAP(args.ssl, server, int(port) , args.n, args.user)
    try:
        server_Imap.start()
    except KeyboardInterrupt:
        server_Imap.stop()


