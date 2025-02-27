import sys
sys.path.append("./")
from fastapi import status

error_occured = {
    "code":500,
    "message":"Error occured"
}

dept_not_found = {
    "code":404,
    "message":"Selected department not supported at the moment."
}

payment_processing = {
    "code":status.HTTP_409_CONFLICT,
    "message":"Your have an Existing payment, Kindly hold on for confirmation."
}

payment_not_found = {
    "code":404,
    "message":"Entered Matric number has no record."
}

payment_session_not_found = {
    "code":404,
    "message":"No records for selected session"
}

invalid_session = {
    "code":status.HTTP_422_UNPROCESSABLE_ENTITY,
    "message":"Session must be in the format '2023/2024' "
}

created = {
    "code":201,
    "message":"created successfully",

}

updated = {
    "code":200,
    "message":"updated successfully",

}

not_found = {
    "code":404,
    "message":"not found or missing",
}
