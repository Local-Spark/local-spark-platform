"""Build an ephemeral feed-analysis input without doing IO or proving provenance.

Only a trusted activity may use this data after verifying the selected profile,
association version, run ownership, budgets and fences. This object contains
third-party content: never serialize it to Temporal, logs, audit, or storage.
No image is fetched, and no analysis or cleanup is performed here.
"""

import re
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.adapters.apify_instagram_feed import InstagramFeedPost, InstagramFeedResult, SubmittedInstagramFeed, _image_url
from app.schemas.owner_references import instagram_handle


class FeedAnalysisInputError(ValueError):
    """A stable error without account details, URLs or post content."""


@dataclass(frozen=True, repr=False)
class EphemeralFeedAnalysisInput:
    reference_id: UUID
    association_version: int
    run: SubmittedInstagramFeed
    posts: tuple[InstagramFeedPost, ...]
    coverage: Literal["unconfirmed", "partial"]


def build_feed_analysis_input(
    reference_id: UUID,
    association_version: int,
    expected_handle: str,
    run: SubmittedInstagramFeed,
    result: InstagramFeedResult,
) -> EphemeralFeedAnalysisInput:
    """Check bounded in-memory structure and preserve explicit partiality.

    A matching handle or syntactically valid provider IDs is not provenance or
    proof of ownership. Image URL host checks do not make downloading safe.
    """
    if (
        not isinstance(reference_id, UUID)
        or type(association_version) is not int
        or not 0 < association_version <= 9_223_372_036_854_775_807
        or not isinstance(expected_handle, str)
        or not isinstance(run, SubmittedInstagramFeed)
        or not isinstance(result, InstagramFeedResult)
        or not isinstance(run.submission_id, UUID)
        or not isinstance(run.username, str)
        or type(run.results_limit) is not int
        or not 1 <= run.results_limit <= 20
    ):
        raise FeedAnalysisInputError("REFERENCE_FEED_ANALYSIS_INPUT_INVALID")
    try:
        expected = instagram_handle(expected_handle)
        if instagram_handle(run.username) != run.username or run.username != expected:
            raise ValueError
    except ValueError:
        raise FeedAnalysisInputError("REFERENCE_FEED_ANALYSIS_INPUT_INVALID") from None
    ids = (run.run_id, run.dataset_id, run.key_value_store_id, run.request_queue_id, run.build_id)
    if (
        any(not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is None for value in ids)
        or not isinstance(run.build_number, str)
        or len(run.build_number) > 64
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", run.build_number) is None
        or result.state not in ("available", "partial")
        or result.coverage not in ("unconfirmed", "partial")
        or (result.state == "available" and result.coverage != "unconfirmed")
        or (result.state == "partial" and result.coverage != "partial")
        or not isinstance(result.posts, tuple)
        or not 1 <= len(result.posts) <= run.results_limit
    ):
        raise FeedAnalysisInputError("REFERENCE_FEED_ANALYSIS_INPUT_INVALID")
    seen: set[str] = set()
    for post in result.posts:
        if (
            not isinstance(post, InstagramFeedPost)
            or not isinstance(post.post_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", post.post_id) is None
            or post.post_id in seen
            or (post.caption is not None and (not isinstance(post.caption, str) or len(post.caption) > 10_000))
            or not isinstance(post.image_urls, tuple)
            or any(not isinstance(url, str) or _image_url(url) != url for url in post.image_urls)
            or len(set(post.image_urls)) != len(post.image_urls)
            or (post.caption is None and not post.image_urls)
        ):
            raise FeedAnalysisInputError("REFERENCE_FEED_ANALYSIS_INPUT_INVALID")
        seen.add(post.post_id)
    return EphemeralFeedAnalysisInput(reference_id, association_version, run, result.posts, result.coverage)
