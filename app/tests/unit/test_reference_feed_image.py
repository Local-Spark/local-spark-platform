"""Image validation and request fencing use synthetic bytes and mock HTTP only."""

import io
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from PIL import Image

from app.adapters.apify_instagram_feed import InstagramFeedPost, SubmittedInstagramFeed
from app.adapters.reference_feed_image import FeedImageError, MockFeedImageDownloader, _image

_URL = "https://scontent.cdninstagram.com/synthetic.png?token=private"


def picture(size=(2, 2), fmt="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", size).save(buffer, format=fmt)
    return buffer.getvalue()


def run():
    return SubmittedInstagramFeed(uuid4(), "profile", "run", "dataset", "kv", "queue", "1.2.3", "build", 20)


def post():
    return InstagramFeedPost("post", "private caption", (_URL,))


class Guard:
    def __init__(self, result=True):
        self.result, self.calls = result, []

    async def authorize(self, operation, intent):
        self.calls.append((operation, intent))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


_MISSING = object()


def downloader(handler, guard=_MISSING, **changes):
    options = {
        "guard": Guard() if guard is _MISSING else guard,
        "enabled": True,
        "transport": httpx.MockTransport(handler),
    }
    return MockFeedImageDownloader(**{**options, **changes})


async def test_fetch_requires_guard_and_keeps_bytes_in_memory(caplog):
    guard, operation, source = Guard(), uuid4(), run()
    content = picture()

    def handler(request):
        assert len(guard.calls) == 1
        selected, intent = guard.calls[0]
        assert selected == operation and intent.run == source and intent.post_id == "post" and intent.url == _URL
        assert request.method == "GET" and str(request.url) == _URL and "private" not in repr(intent)
        return httpx.Response(200, content=content, headers={"content-type": "image/png"})

    image = await downloader(handler, guard).fetch(source, post(), _URL, operation)
    assert image.content == content and image.mime_type == "image/png" and (image.width, image.height) == (2, 2)
    assert "private" not in repr(image) and "token" not in caplog.text


async def test_explicit_live_image_transport_preserves_host_guard_and_bounds(monkeypatch):
    from app.adapters.reference_feed_image import FeedImageDownloader

    created, guard = [], Guard()

    def factory(**kwargs):
        created.append(kwargs)

        def respond(request):
            assert guard.calls and request.url.host == "scontent.cdninstagram.com"
            assert "authorization" not in request.headers
            return httpx.Response(200, content=picture(), headers={"content-type": "image/png"})

        return httpx.MockTransport(respond)

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", factory)
    client = FeedImageDownloader(guard, enabled=True, network_enabled=True)
    result = await client.fetch(run(), post(), _URL, uuid4())
    assert result.width == 2 and created == [{"retries": 0, "trust_env": False}]
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_INPUT_INVALID"):
        await client.fetch(run(), post(), "http://127.0.0.1/", uuid4())
    assert len(created) == 1


async def test_fetch_can_select_an_image_beyond_twenty_in_a_carousel():
    urls = tuple(f"https://scontent.cdninstagram.com/{i}.png" for i in range(25))
    source = replace(post(), image_urls=urls)
    image = await downloader(
        lambda _: httpx.Response(200, content=picture(), headers={"content-type": "image/png"})
    ).fetch(run(), source, urls[-1], uuid4())
    assert (image.width, image.height) == (2, 2)


@pytest.mark.parametrize(
    "change",
    [
        {"enabled": False},
        {"guard": None},
        {"transport": None},
        {"transport": httpx.AsyncHTTPTransport()},
    ],
)
async def test_only_enabled_mock_transport_and_guard_are_allowed(change):
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_DISABLED"):
        await downloader(lambda _: pytest.fail("no HTTP"), **change).fetch(run(), post(), _URL, uuid4())


@pytest.mark.parametrize("result", [False, 1, RuntimeError("private error")])
async def test_guard_denial_never_dispatches(result):
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_NOT_AUTHORIZED"):
        await downloader(lambda _: pytest.fail("no HTTP"), Guard(result)).fetch(run(), post(), _URL, uuid4())


@pytest.mark.parametrize(
    "change",
    [
        {"submission_id": "bad"},
        {"username": None},
        {"username": "Profile"},
        {"username": "a..b"},
        {"run_id": "bad/id"},
        {"dataset_id": None},
        {"build_number": "latest"},
        {"results_limit": 0},
        {"results_limit": True},
        {"results_limit": 21},
    ],
)
async def test_invalid_run_never_reaches_guard(change):
    guard = Guard()
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_INPUT_INVALID"):
        await downloader(lambda _: pytest.fail("no HTTP"), guard).fetch(replace(run(), **change), post(), _URL, uuid4())
    assert guard.calls == []


@pytest.mark.parametrize(
    "source,item,url,operation",
    [
        (None, post(), _URL, uuid4()),
        (run(), None, _URL, uuid4()),
        (run(), post(), None, uuid4()),
        (run(), post(), _URL, "bad"),
        (run(), replace(post(), post_id="bad/id"), _URL, uuid4()),
        (run(), replace(post(), image_urls=[]), _URL, uuid4()),
        (run(), post(), "https://127.0.0.1/private", uuid4()),
        (run(), post(), "https://cdninstagram.com.attacker.example/x", uuid4()),
        (run(), post(), "https://user:pass@cdninstagram.com/x", uuid4()),
        (run(), post(), "https://cdninstagram.com/other", uuid4()),
    ],
)
async def test_invalid_source_url_or_operation_never_reaches_guard(source, item, url, operation):
    guard = Guard()
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_INPUT_INVALID"):
        await downloader(lambda _: pytest.fail("no HTTP"), guard).fetch(source, item, url, operation)
    assert guard.calls == []


@pytest.mark.parametrize("status", [201, 301, 302, 307, 308, 400, 500])
async def test_redirects_and_unsuccessful_http_are_never_followed(status):
    called = []

    def handler(request):
        called.append(request.url.host)
        return httpx.Response(status, headers={"location": "http://127.0.0.1/private"})

    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_UNAVAILABLE"):
        await downloader(handler).fetch(run(), post(), _URL, uuid4())
    assert called == ["scontent.cdninstagram.com"]


@pytest.mark.parametrize(
    "headers,body",
    [
        ({"content-type": "text/html"}, b"bad"),
        ({"content-type": "image/png", "content-length": "bad"}, b"x"),
        ({"content-type": "image/png", "content-length": "99999999999"}, b"x"),
        ({"content-type": "image/png", "content-length": "5242881"}, b"x"),
        ({"content-type": "image/png", "content-length": "1"}, picture()),
        ({"content-type": "image/png"}, b"not-an-image"),
        ({"content-type": "image/jpeg"}, picture()),
        ({"content-type": "image/png"}, picture((4097, 1))),
        ({"content-type": "image/png"}, picture((4000, 4000))),
    ],
)
async def test_bad_content_mime_and_size_are_rejected(headers, body):
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_INVALID"):
        await downloader(lambda _: httpx.Response(200, headers=headers, content=body)).fetch(
            run(), post(), _URL, uuid4()
        )


class HugeStream(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b"x" * (5 * 1024 * 1024 + 1)


async def test_stream_limit_is_enforced_even_without_content_length():
    response = httpx.Response(200, headers={"content-type": "image/png"}, stream=HugeStream())
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_INVALID"):
        await downloader(lambda _: response).fetch(run(), post(), _URL, uuid4())


async def test_transport_exception_has_no_url_or_payload():
    def handler(_):
        raise RuntimeError("secret-url")

    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_UNAVAILABLE") as error:
        await downloader(handler).fetch(run(), post(), _URL, uuid4())
    assert "secret-url" not in str(error.value) and "token" not in str(error.value)


def test_animation_and_decoder_failure_are_rejected(monkeypatch):
    data = picture()

    class FakeImage:
        size = (2, 2)
        format = "PNG"
        n_frames = 2

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(Image, "open", lambda *_: FakeImage())
    with pytest.raises(FeedImageError, match="REFERENCE_FEED_IMAGE_INVALID"):
        _image(data, "image/png")
