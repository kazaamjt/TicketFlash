"""
Request Objects describe what an http request should look like.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel

from ..backend.objects import User, UserMetadata

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

    def create_user(self) -> tuple[User, UserMetadata]:
        """
        Creates a user in the backend.
        """
        _id = uuid4()
        created_at = datetime.now()
        user = User(id=_id, email=self.email, created_at=created_at)
        user_metadata = UserMetadata(
            id=_id,
            first_name=self.first_name,
            last_name=self.last_name,
            address=self.address,
            postal_code=self.postal_code,
            city=self.city,
            telephone=self.telephone,
        )

        return user, user_metadata
