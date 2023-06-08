# TODO: populate this when we have a better idea of what we need
from pydantic import BaseModel, conint, validator  # pylint:disable=no-name-in-module


class Extract(BaseModel):
    """
    Extract class for extracting data from API.
    """
