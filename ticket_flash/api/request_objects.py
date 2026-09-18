"""
Request Objects describe what an http request should look like.
"""

from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel

from ..backend.objects import User, UserMetadata
from ..types import now

if TYPE_CHECKING:
    from ..backend.database import Database


class HTTPRequestModel(BaseModel):
    """
    What HTTP requests should look like.
    """


class UserCreateRequest(HTTPRequestModel):
    """
    Data required to create a user.
    """

    email: str
    first_name: str | None = None
    last_name: str | None = None
    address: str | None = None
    postal_code: int | None = None
    city: str | None = None
    telephone: str | None = None

    async def create_user(self, db: "Database") -> tuple[User, UserMetadata]:
        """
        Creates a user in the backend.
        """
        _id = uuid4()
        created_at = now()
        user = User(id=_id, email=self.email)
        user_metadata = UserMetadata(
            user_id=_id,
            created_at=created_at,
            first_name=self.first_name,
            last_name=self.last_name,
            address=self.address,
            postal_code=self.postal_code,
            city=self.city,
            telephone=self.telephone,
        )

        await user.insert(db)
        await user_metadata.insert(db)

        return user, user_metadata
