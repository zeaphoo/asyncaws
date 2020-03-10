
import sys
import xml.etree.cElementTree



class AsyncStreamingBody(object):

    def __init__(self, raw_stream, content_length):
        self._raw_stream = raw_stream
        self._content_length = content_length
        self._amount_read = 0

    async def read(self):
        chunk = await self._raw_stream.aread()
        self._amount_read += len(chunk)
        return chunk

    async def __aiter__(self):
        """Return an iterator to yield 1k chunks from the raw stream.
        """
        return await self._raw_stream.iter_bytes()


    async def iter_lines(self,):
        return await self._raw_stream.iter_lines()

    async def iter_chunks(self):
        """Return an iterator to yield chunks of chunk_size bytes from the raw
        stream.
        """
        return await self._raw_stream.iter_bytes()

    async def close(self):
        """Close the underlying http response stream."""
        await self._raw_stream.aclose()
