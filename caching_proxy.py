import argparse
import http.server
import os
import pickle
import signal
import socketserver
import ssl
import sys
import urllib.request
import urllib.parse


CACHE = {}
CACHE_FILE = 'cache.pkl'

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'rb') as f:
        CACHE = pickle.load(f)

# Disable SSL verification
context = ssl._create_unverified_context()

def signal_handler(sig, frame):
    """Handle Ctrl+C when user exits the program.
    """
    print('Interrupt received, shutting down...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class Handler(http.server.SimpleHTTPRequestHandler):
    """This is the handler class used by the socketserver.TCPServer class to
    handle the incoming http calls.

    Args:
        http (SimpleHTTPRequestHandler)): the parent class with access to methods for
        handling http.
    """
    def do_GET(self):
        """This method handles the GET request by checking if the url exists
        within the cache, if yes then the response is returned from the cache.
        If not, the origin url is opened and stored in the cache and a 301(redirect)
        response code is returned.
        """
        parsed_url = urllib.parse.urlparse(self.path)
        url = ORIGIN + parsed_url.geturl()

        #set_trace()
        if url in CACHE:
            self.send_response(200)
            self.send_header('X-Cache', 'HIT')
            self.end_headers()
            self.wfile.write(CACHE[url])
        else:
            try:
                with urllib.request.urlopen(url, context=context) as response:
                    content = response.read()
                    CACHE[url] = content

                    self.send_response(301)
                    self.send_header('X-Cache', 'MISS')
                    self.end_headers()
                    self.wfile.write(CACHE[url])

                    with open(CACHE_FILE, 'wb') as f:
                        pickle.dump(CACHE, f)
            except urllib.error.URLError as error:
                self.send_error(500, f'Error fetching {url}: {error.reason}')
            except Exception as error:
                self.send_error(500, f'Unexpexted error: {error}')


def clear_cache():
    """Remove the cache from disk.
    """
    if os.path.exists(CACHE_FILE):
            os.unlink(CACHE_FILE)
    print('Cache removed')
    sys.exit(0)

def caching_proxy(host: str, port: int) -> None:
    """This starts the server on the specified interface and port.

    Args:
        host (str): the interface which the server with listen on.
        port (int): the traffic port used by the server.
    """
    with socketserver.TCPServer((host, port), Handler) as httpd:
        print(f'Server listening on port {port}. Ctrl+C to quit.')
        httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='caching-proxy',
        description='A caching proxy server',
        usage='caching-proxy --port <number> --origin <url>'
    )

    parser.add_argument('--port', help='listening port', type=int, default=8080)
    parser.add_argument('--origin', help='original traffic destination')
    parser.add_argument('--clear-cache', action='store_true', help='clear the cached data')
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()


    PORT = args.port
    ORIGIN = args.origin

    caching_proxy('', PORT)
