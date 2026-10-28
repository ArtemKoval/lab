"""Reads the secret from the environment in place of google.colab.userdata."""
import os


def get(key):
    """Return the secret for the name. Raise KeyError with guidance when the name is absent."""
    try:
        return os.environ[key]
    except KeyError:
        raise KeyError(
            f"Secret {key!r} is not in the environment. Add it to the .env file at the repo root."
        )
