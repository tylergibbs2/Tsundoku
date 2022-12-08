class ExprDict(dict):
    def __missing__(self, value: str) -> str:
        return value


def normalize_resolution(original: str) -> str:
    """
    Normalize a resolution string.

    Parameters
    ----------
    original: str
        The original resolution string.

    Returns
    -------
    str
        The normalized resolution string or the original
        if normalization was not possible.
    """
    original = original.lower().strip()
    if "x" in original:
        try:
            width, height, *_ = original.split("x")
            width, height = int(width.strip()), int(height.strip())
        except ValueError:
            return original.replace(" ", "")

        if height == 4320:
            return "8k"
        elif height == 3840:
            return "4k"
        elif height == 1080:
            return "1080p"
        elif height == 720:
            return "720p"
        elif height == 480:
            return "480p"
        elif height == 360:
            return "360p"

        return f"{width}x{height}"
    elif original.endswith("p"):
        if original == "4320p":
            return "8k"
        elif original == "2160p":
            return "4k"

    return original
