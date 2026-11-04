"""Only bounded, explicitly partial feed data can enter a private analysis input."""

from dataclasses import replace
from uuid import uuid4

import pytest

from app.adapters.apify_instagram_feed import InstagramFeedPost, InstagramFeedResult, SubmittedInstagramFeed
from app.services.reference_feed_analysis_input import FeedAnalysisInputError, build_feed_analysis_input


def values():
    run = SubmittedInstagramFeed(uuid4(), "profile", "run", "dataset", "kv", "queue", "1.2.3", "build", 20)
    post = InstagramFeedPost("post-1", "private caption", ("https://scontent.cdninstagram.com/photo",))
    return {
        "reference_id": uuid4(),
        "association_version": 1,
        "expected_handle": "@Profile",
        "run": run,
        "result": InstagramFeedResult("partial", (post,), "partial"),
    }


def test_preserves_exact_profile_run_and_partial_coverage_without_exposing_repr():
    args = values()
    result = build_feed_analysis_input(**args)
    assert result.run == args["run"] and result.posts == args["result"].posts and result.coverage == "partial"
    assert result.reference_id == args["reference_id"] and result.association_version == 1
    assert "private" not in repr(result) and "profile" not in repr(result) and "cdninstagram" not in repr(result)
    full = build_feed_analysis_input(
        **{**args, "result": replace(args["result"], state="available", coverage="unconfirmed")}
    )
    assert full.coverage == "unconfirmed"


@pytest.mark.parametrize(
    "change",
    [
        {"reference_id": "bad"},
        {"association_version": True},
        {"association_version": 0},
        {"association_version": 2**63},
        {"expected_handle": None},
        {"expected_handle": "other"},
        {"expected_handle": "a..b"},
        {"run": None},
        {"result": None},
    ],
)
def test_invalid_identity_never_exposes_content(change):
    with pytest.raises(FeedAnalysisInputError, match="REFERENCE_FEED_ANALYSIS_INPUT_INVALID") as error:
        build_feed_analysis_input(**{**values(), **change})
    assert "private" not in str(error.value)


@pytest.mark.parametrize(
    "change",
    [
        {"submission_id": "bad"},
        {"username": None},
        {"username": "Profile"},
        {"run_id": "bad/id"},
        {"dataset_id": None},
        {"build_number": "latest"},
        {"build_number": "1." + "9" * 64},
        {"results_limit": True},
        {"results_limit": 0},
        {"results_limit": 21},
    ],
)
def test_invalid_run_is_rejected(change):
    args = values()
    with pytest.raises(FeedAnalysisInputError, match="REFERENCE_FEED_ANALYSIS_INPUT_INVALID"):
        build_feed_analysis_input(**{**args, "run": replace(args["run"], **change)})


@pytest.mark.parametrize(
    "change",
    [
        {"state": "pending"},
        {"state": "unavailable"},
        {"coverage": "unknown"},
        {"state": "available", "coverage": "partial"},
        {"state": "partial", "coverage": "unconfirmed"},
        {"posts": []},
        {"posts": ()},
    ],
)
def test_unavailable_or_inconsistent_results_are_rejected(change):
    args = values()
    with pytest.raises(FeedAnalysisInputError, match="REFERENCE_FEED_ANALYSIS_INPUT_INVALID"):
        build_feed_analysis_input(**{**args, "result": replace(args["result"], **change)})


def test_more_posts_than_configured_limit_or_duplicates_are_rejected():
    args = values()
    post = args["result"].posts[0]
    for posts in ((post, post), tuple(replace(post, post_id=str(i)) for i in range(21))):
        with pytest.raises(FeedAnalysisInputError, match="REFERENCE_FEED_ANALYSIS_INPUT_INVALID"):
            build_feed_analysis_input(**{**args, "result": replace(args["result"], posts=posts)})


def test_carousel_more_than_twenty_images_remains_complete_in_memory():
    args = values()
    urls = tuple(f"https://scontent.cdninstagram.com/{i}" for i in range(25))
    item = replace(args["result"].posts[0], image_urls=urls)
    result = build_feed_analysis_input(**{**args, "result": replace(args["result"], posts=(item,))})
    assert result.posts[0].image_urls == urls and result.coverage == "partial"


@pytest.mark.parametrize(
    "post",
    [
        None,
        InstagramFeedPost("bad/id", "x", ()),
        InstagramFeedPost(None, "x", ()),
        InstagramFeedPost("id", 42, ()),
        InstagramFeedPost("id", "x" * 10001, ()),
        InstagramFeedPost("id", "x", []),
        InstagramFeedPost("id", "x", ("http://bad",)),
        InstagramFeedPost("id", "x", ("https://scontent.cdninstagram.com/x",) * 2),
        InstagramFeedPost("id", None, ()),
    ],
)
def test_bad_post_or_image_url_is_rejected(post):
    args = values()
    with pytest.raises(FeedAnalysisInputError, match="REFERENCE_FEED_ANALYSIS_INPUT_INVALID"):
        build_feed_analysis_input(**{**args, "result": replace(args["result"], posts=(post,))})
