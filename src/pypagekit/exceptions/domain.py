"""Domain exceptions raised by PyPageKit."""


class PyPageKitError(Exception):
    """Base exception for all PyPageKit-specific failures."""


class DomainError(PyPageKitError):
    """Base exception for invalid domain operations or states."""


class ValidationError(DomainError):
    """Base exception for domain validation failures."""


class InvalidPageTitleError(ValidationError):
    """Raised when a page title is empty after normalization."""


class InvalidPageLanguageError(ValidationError):
    """Raised when a page language value is empty after normalization."""


class InvalidPageContentError(ValidationError):
    """Raised when a page contains an object that is not Content."""


class InvalidHeadingLevelError(ValidationError):
    """Raised when a heading level is outside the supported 1..6 range."""


class InvalidContainerChildError(ValidationError):
    """Raised when a container includes an object that is not Content."""


class InvalidLinkHrefError(ValidationError):
    """Raised when a link destination is structurally empty."""


class InvalidImageSourceError(ValidationError):
    """Raised when an image source reference is structurally empty."""


class InvalidAttributeError(ValidationError):
    """Base exception for invalid author-facing attribute metadata."""


class InvalidClassTokenError(InvalidAttributeError):
    """Raised when a CSS class token is empty or contains whitespace."""


class InvalidDataAttributeNameError(InvalidAttributeError):
    """Raised when a data attribute suffix is structurally invalid."""


class InvalidAriaAttributeNameError(InvalidAttributeError):
    """Raised when an ARIA attribute suffix is structurally invalid."""


class InvalidLayoutError(ValidationError):
    """Base exception for invalid layout structure."""


class InvalidLayoutRegionNameError(InvalidLayoutError):
    """Raised when a layout region name is structurally invalid."""


class InvalidLayoutRegionChildError(InvalidLayoutError):
    """Raised when a layout region contains an object that is not Content."""


class InvalidLayoutRegionResultError(InvalidLayoutError):
    """Raised when Layout.regions() yields an object that is not LayoutRegion."""


class DuplicateLayoutRegionError(InvalidLayoutError):
    """Raised when a layout declares the same region name more than once."""



class InvalidSlotError(ValidationError):
    """Base exception for invalid slot composition."""


class InvalidSlotNameError(InvalidSlotError):
    """Raised when a slot name is structurally invalid."""


class InvalidSlotChildError(InvalidSlotError):
    """Raised when slot content contains an object that is not Content."""


class InvalidSlotBindingError(InvalidSlotError):
    """Raised when a slotted component provides an invalid template or bindings."""


class MissingRequiredSlotError(InvalidSlotError):
    """Raised when a required slot has no explicit binding."""


class UnknownSlotBindingError(InvalidSlotError):
    """Raised when bindings contain a name absent from the template."""


class DuplicateSlotError(InvalidSlotError):
    """Raised when a template declares the same slot name more than once."""
