"""
IMS Status Info schemas for Open Badges v3.0 error responses
Reference: https://www.imsglobal.org/spec/ob/v3p0/#imsx_statusinfo
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ImsxCodeMajorEnum(str, Enum):
    """Code major values"""
    FAILURE = "failure"
    PROCESSING = "processing"
    SUCCESS = "success"
    UNSUPPORTED = "unsupported"


class ImsxSeverityEnum(str, Enum):
    """Severity values"""
    ERROR = "error"
    STATUS = "status"
    WARNING = "warning"


class ImsxCodeMinorFieldValueEnum(str, Enum):
    """Code minor field values"""
    FORBIDDEN = "forbidden"
    FULLSUCCESS = "fullsuccess"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    INVALID_DATA = "invalid_data"
    INVALID_QUERY_PARAMETER = "invalid_query_parameter"
    MISDIRECTED_REQUEST = "misdirected_request"
    NOT_ACCEPTABLE = "not_acceptable"
    NOT_ALLOWED = "not_allowed"
    NOT_FOUND = "not_found"
    NOT_MODIFIED = "not_modified"
    SERVER_BUSY = "server_busy"
    UNAUTHORIZEDREQUEST = "unauthorizedrequest"
    UNKNOWN = "unknown"


class ImsxCodeMinorField(BaseModel):
    """A single code minor status code"""
    imsx_codeMinorFieldName: str = Field(
        ...,
        description="This should contain the identity of the system that has produced the code minor status code report."
    )
    imsx_codeMinorFieldValue: ImsxCodeMinorFieldValueEnum = Field(
        ...,
        description="The code minor status code (this is a value from the corresponding enumerated vocabulary)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "imsx_codeMinorFieldName": "system",
                "imsx_codeMinorFieldValue": "forbidden"
            }
        }


class ImsxCodeMinor(BaseModel):
    """Container for the set of code minor status codes"""
    imsx_codeMinorField: List[ImsxCodeMinorField] = Field(
        ...,
        min_length=1,
        description="Each reported code minor status code."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "imsx_codeMinorField": [
                    {
                        "imsx_codeMinorFieldName": "system",
                        "imsx_codeMinorFieldValue": "forbidden"
                    }
                ]
            }
        }


class ImsxStatusInfo(BaseModel):
    """Container for the status code and associated information returned within HTTP messages"""
    imsx_codeMajor: ImsxCodeMajorEnum = Field(
        ...,
        description="The code major value (from the corresponding enumerated vocabulary)."
    )
    imsx_severity: ImsxSeverityEnum = Field(
        ...,
        description="The severity value (from the corresponding enumerated vocabulary)."
    )
    imsx_description: Optional[str] = Field(
        None,
        description="A human readable description supplied by the entity creating the status code information."
    )
    imsx_codeMinor: Optional[ImsxCodeMinor] = Field(
        None,
        description="This is the container for the set of code minor status codes reported in the responses."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "imsx_codeMajor": "failure",
                "imsx_severity": "error",
                "imsx_description": "The request was invalid or cannot be served.",
                "imsx_codeMinor": {
                    "imsx_codeMinorField": [
                        {
                            "imsx_codeMinorFieldName": "system",
                            "imsx_codeMinorFieldValue": "invalid_data"
                        }
                    ]
                }
            }
        }


def create_imsx_status_info(
    code_major: ImsxCodeMajorEnum,
    severity: ImsxSeverityEnum,
    description: str,
    code_minor_value: Optional[ImsxCodeMinorFieldValueEnum] = None,
    code_minor_name: str = "system"
) -> ImsxStatusInfo:
    """Helper function to create ImsxStatusInfo"""
    code_minor = None
    if code_minor_value:
        code_minor = ImsxCodeMinor(
            imsx_codeMinorField=[
                ImsxCodeMinorField(
                    imsx_codeMinorFieldName=code_minor_name,
                    imsx_codeMinorFieldValue=code_minor_value
                )
            ]
        )
    
    return ImsxStatusInfo(
        imsx_codeMajor=code_major,
        imsx_severity=severity,
        imsx_description=description,
        imsx_codeMinor=code_minor
    )


def map_http_status_to_imsx(status_code: int, description: str = None) -> ImsxStatusInfo:
    """Map HTTP status codes to ImsxStatusInfo"""
    if status_code == 400:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "The server cannot or will not process the request due to something that is perceived to be a client error.",
            ImsxCodeMinorFieldValueEnum.INVALID_DATA
        )
    elif status_code == 401:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "The request has not been applied because it lacks valid authentication credentials for the target resource.",
            ImsxCodeMinorFieldValueEnum.UNAUTHORIZEDREQUEST
        )
    elif status_code == 403:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "The server understood the request but refuses to fulfill it.",
            ImsxCodeMinorFieldValueEnum.FORBIDDEN
        )
    elif status_code == 404:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "The origin server did not find a current representation for the target resource or is not willing to disclose that one exists.",
            ImsxCodeMinorFieldValueEnum.NOT_FOUND
        )
    elif status_code == 405:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "The server does not allow the method.",
            ImsxCodeMinorFieldValueEnum.NOT_ALLOWED
        )
    elif status_code == 500:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "An internal server error occurred.",
            ImsxCodeMinorFieldValueEnum.INTERNAL_SERVER_ERROR
        )
    else:
        return create_imsx_status_info(
            ImsxCodeMajorEnum.FAILURE,
            ImsxSeverityEnum.ERROR,
            description or "An error occurred.",
            ImsxCodeMinorFieldValueEnum.UNKNOWN
        )

