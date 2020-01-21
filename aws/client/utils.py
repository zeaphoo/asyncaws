from urllib.parse import quote

SAFE_CHARS = '-._~'


def normalize_url_path(path):
    if not path:
        return '/'
    return remove_dot_segments(path)


def remove_dot_segments(url):
    # RFC 3986, section 5.2.4 "Remove Dot Segments"
    # Also, AWS services require consecutive slashes to be removed,
    # so that's done here as well
    if not url:
        return ''
    input_url = url.split('/')
    output_list = []
    for x in input_url:
        if x and x != '.':
            if x == '..':
                if output_list:
                    output_list.pop()
            else:
                output_list.append(x)

    if url[0] == '/':
        first = '/'
    else:
        first = ''
    if url[-1] == '/' and output_list:
        last = '/'
    else:
        last = ''
    return first + '/'.join(output_list) + last


def percent_encode_sequence(mapping, safe=SAFE_CHARS):
    """Urlencode a dict or list into a string.

    This is similar to urllib.urlencode except that:

    * It uses quote, and not quote_plus
    * It has a default list of safe chars that don't need
      to be encoded, which matches what AWS services expect.

    If any value in the input ``mapping`` is a list type,
    then each list element wil be serialized.  This is the equivalent
    to ``urlencode``'s ``doseq=True`` argument.

    This function should be preferred over the stdlib
    ``urlencode()`` function.

    :param mapping: Either a dict to urlencode or a list of
        ``(key, value)`` pairs.

    """
    encoded_pairs = []
    if hasattr(mapping, 'items'):
        pairs = mapping.items()
    else:
        pairs = mapping
    for key, value in pairs:
        if isinstance(value, list):
            for element in value:
                encoded_pairs.append('%s=%s' % (percent_encode(key),
                                                percent_encode(element)))
        else:
            encoded_pairs.append('%s=%s' % (percent_encode(key),
                                            percent_encode(value)))
    return '&'.join(encoded_pairs)


def percent_encode(input_str, safe=SAFE_CHARS):
    """Urlencodes a string.

    Whereas percent_encode_sequence handles taking a dict/sequence and
    producing a percent encoded string, this function deals only with
    taking a string (not a dict/sequence) and percent encoding it.

    If given the binary type, will simply URL encode it. If given the
    text type, will produce the binary type by UTF-8 encoding the
    text. If given something else, will convert it to the text type
    first.
    """
    # If its not a binary or text string, make it a text string.
    if not isinstance(input_str, (bytes, str)):
        input_str = str(input_str)
    # If it's not bytes, make it bytes by UTF-8 encoding it.
    if not isinstance(input_str, bytes):
        input_str = input_str.encode('utf-8')
    return quote(input_str, safe=safe)