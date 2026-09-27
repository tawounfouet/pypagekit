from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Content, Image
from pypagekit.domain import Media
from pypagekit.exceptions import InvalidImageSourceError


def test_media_is_content() -> None:
    assert issubclass(Media, Content)


def test_image_is_media() -> None:
    assert issubclass(Image, Media)


def test_image_preserves_src_and_alt_exactly() -> None:
    image = Image(src=" /assets/logo.png ", alt="  Logo & mark  ")

    assert image.src == " /assets/logo.png "
    assert image.alt == "  Logo & mark  "


def test_image_accepts_relative_source() -> None:
    assert Image(src="/assets/logo.png", alt="Logo").src == "/assets/logo.png"


def test_image_accepts_external_source_reference() -> None:
    source = "https://example.com/image.png"

    assert Image(src=source, alt="Example").src == source


def test_image_accepts_empty_alt_for_decorative_images() -> None:
    image = Image(src="/assets/decorative.png", alt="")

    assert image.alt == ""


def test_image_preserves_unicode_alt_text() -> None:
    alt = "Café 東京 你好 🔥"

    assert Image(src="/image.png", alt=alt).alt == alt


@pytest.mark.parametrize("src", ["", " ", "\n\t"])
def test_image_rejects_empty_source_after_whitespace_check(src: str) -> None:
    with pytest.raises(InvalidImageSourceError, match="must not be empty"):
        Image(src=src, alt="Image")


def test_image_rejects_non_string_source() -> None:
    with pytest.raises(TypeError, match="Image src must be a string"):
        Image(src=42, alt="Image")  # type: ignore[arg-type]


def test_image_rejects_non_string_alt() -> None:
    with pytest.raises(TypeError, match="Image alt must be a string"):
        Image(src="/image.png", alt=42)  # type: ignore[arg-type]


def test_image_is_immutable() -> None:
    image = Image(src="/image.png", alt="Image")

    with pytest.raises(FrozenInstanceError):
        image.src = "/changed.png"  # type: ignore[misc]
