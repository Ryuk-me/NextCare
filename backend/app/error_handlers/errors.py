# from fastapi.responses import JSONResponse
from fastapi import HTTPException, status


INVALID_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials")

NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="not found")

TOKEN_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

FORBIDDEN_ACTION_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="not authorised to perform this action")

ALREADY_EXIST_CLINIC = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="clinic already exist for this doctor")
