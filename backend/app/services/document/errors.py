class DocumentError(Exception):
    """Base for all document-processing failures; always caught and turned
    into a useful status instead of crashing the upload request."""


class UnsupportedFileTypeError(DocumentError):
    pass


class EmptyDocumentError(DocumentError):
    pass


class FileTooLargeError(DocumentError):
    pass


class DocumentExtractionError(DocumentError):
    pass
