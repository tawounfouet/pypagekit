"""Page aggregate for the PyPageKit core domain."""

from collections.abc import Iterable
from dataclasses import dataclass

from pypagekit.exceptions import (
    InvalidPageContentError,
    InvalidPageLanguageError,
    InvalidPageTitleError,
)

from .base import Content, Node


@dataclass(frozen=True, slots=True, init=False)
class Page(Node):
    """Root document object for a PyPageKit page.

    The constructor accepts any iterable of :class:`Content` for ergonomics,
    while the stored representation is normalized to an immutable tuple.
    """

    title: str
    content: tuple[Content, ...]
    lang: str
    description: str | None

    def __init__(
        self,
        title: str,
        content: Iterable[Content] = (),
        *,
        lang: str = "en",
        description: str | None = None,
    ) -> None:
        if not isinstance(title, str):
            raise TypeError("Page title must be a string.")
        normalized_title = title.strip()
        if not normalized_title:
            raise InvalidPageTitleError("Page title must not be empty.")

        if not isinstance(lang, str):
            raise TypeError("Page language must be a string.")
        normalized_lang = lang.strip()
        if not normalized_lang:
            raise InvalidPageLanguageError("Page language must not be empty.")

        if description is not None and not isinstance(description, str):
            raise TypeError("Page description must be a string or None.")

        try:
            normalized_content = tuple(content)
        except TypeError as exc:
            raise TypeError("Page content must be an iterable of Content objects.") from exc

        invalid_items = [item for item in normalized_content if not isinstance(item, Content)]
        if invalid_items:
            invalid_type = type(invalid_items[0]).__name__
            raise InvalidPageContentError(
                f"Page content must contain only Content objects; got {invalid_type}."
            )

        object.__setattr__(self, "title", normalized_title)
        object.__setattr__(self, "content", normalized_content)
        object.__setattr__(self, "lang", normalized_lang)
        object.__setattr__(self, "description", description)
