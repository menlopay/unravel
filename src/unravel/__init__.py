from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("unravel-review")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
