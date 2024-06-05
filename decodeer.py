import pickle
import http.client
import http.cookiejar
import urllib.parse


def load_cookies(file_name='cookies.pkl'):
    with open(file_name, "rb") as cookie_file:
        cookies = pickle.load(cookie_file)
    return cookies


def make_request_with_cookies(url, file_name='cookies.pkl'):
    # Load cookies from file
    cookies = load_cookies(file_name)

    # Parse the URL
    parsed_url = urllib.parse.urlparse(url)

    # Setup CookieJar and add cookies to it
    cookie_jar = http.cookiejar.CookieJar()
    for cookie in cookies:
        c = http.cookiejar.Cookie(
            version=0, name=cookie['name'], value=cookie['value'], port=None, port_specified=False,
            domain=cookie['domain'], domain_specified=True, domain_initial_dot=False, path=cookie['path'],
            path_specified=True, secure=cookie['secure'], expires=None, discard=False, comment=None,
            comment_url=None, rest={'HttpOnly': None}, rfc2109=False
        )
        cookie_jar.set_cookie(c)

    # Create an HTTP connection
    conn = http.client.HTTPSConnection(parsed_url.netloc)

    # Create a Cookie header
    cookie_header = '; '.join([f"{c.name}={c.value}" for c in cookie_jar])
    headers = {'Cookie': cookie_header}

    # Make a GET request
    conn.request("GET", parsed_url.path or '/', headers=headers)

    # Get the response
    response = conn.getresponse()
    data = response.read()

    # For demonstration purposes, write the response content to a file
    with open("response.html", "wb") as f:
        f.write(data)

    conn.close()

    return response


# Example usage
response = make_request_with_cookies('https://uclan.unitu.co.uk/Board/Department/1306')
print(response.status, response.reason)
