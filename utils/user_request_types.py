from pydantic import BaseModel


class UserFile(BaseModel):
    file_bytes: bytes
    file_type: str
    filename: str


class UserRequest(BaseModel):
    user_id: int
    text: str | None = None
    file: UserFile | None = None
