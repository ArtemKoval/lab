"""Checking a worker's sign-in: an access token from the auth service, signed with
one of its public keys."""

import os
from functools import cache

import jwt

AUDIENCE = "crm"
# Seconds of difference allowed between the auth service's clock and ours.
CLOCK_LEEWAY = 30


class NotSignedIn(Exception):
    """The token isn't a valid sign-in."""


class OutOfReach(Exception):
    """The auth service's public keys couldn't be fetched to check a sign-in."""


@cache
def public_keys() -> jwt.PyJWKClient:
    """The auth service's public keys, at AUTH_URL. The client keeps the key set it
    fetches for five minutes, and fetches it again for a key it hasn't seen."""
    auth_url = os.environ.get("AUTH_URL", "http://127.0.0.1:8004")
    return jwt.PyJWKClient(f"{auth_url}/jwks.json")


def email_of(token: str) -> str:
    """Return the email of a valid, unexpired sign-in, or raise NotSignedIn, or
    OutOfReach when the service's keys can't be fetched: the sign-in may be fine."""
    try:
        key = public_keys().get_signing_key_from_jwt(token)
        cases = jwt.decode(
            token,
            key,
            algorithms=[key.algorithm_name],
            audience=AUDIENCE,
            leeway=CLOCK_LEEWAY,
            options={"require": ["exp", "email"]},
        )
    except jwt.PyJWKClientConnectionError as error:
        raise OutOfReach(str(error)) from error
    except jwt.PyJWTError as error:
        raise NotSignedIn(str(error)) from error
    return cases["email"]
