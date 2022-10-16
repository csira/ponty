from dataclasses import dataclass
import enum
import logging

from ponty import (
    expect,
    ParsedJsonBody,
    PosIntRouteParameter,
    put,
    raise_status,
    Request,
    startmeup,
)


@dataclass(frozen=True)
class Profile:

    given_name: str
    surname: str
    email: str


class UpdateProfileReq(Request):

    user_id = PosIntRouteParameter()
    body = ParsedJsonBody(Profile)


@put(f"/user/{UpdateProfileReq.user_id}")
@expect(UpdateProfileReq)
async def handler(user_id: int, body: Profile):
    result = await update_profile(
        user_id,
        given_name=body.given_name,
        surname=body.surname,
        email=body.email,
    )
    raise_status(result.value)


class Result(enum.IntEnum):

    SUCCESS = 200
    INVALID = 400
    MISSING = 404


async def update_profile(
    user_id: int,
    *,
    given_name: str,
    surname: str,
    email: str,
) -> Result:
    # write to db, etc
    return Result.SUCCESS


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    startmeup(port=8000)
