

class UVSError(Exception):
    pass


class UVSErrorInvalidSnapshot(UVSError):
    pass


class UVSErrorInvalidTree(UVSError):
    pass


class UVSErrorInvalidFile(UVSError):
    pass


class UVSErrorInvalidDestinationDirectory(UVSError):
    pass


class UVSErrorInvalidRepository(UVSError):
    pass


class UVSErrorTableDoesNotHaveSuchKey(UVSError):
    pass


class UVSErrorTamperDetected(UVSError):
    pass