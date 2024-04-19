import sys
sys.path.append("./")

error_occured = {
    "code":500,
    "message":"error occured"
}

dept_not_found = {
    "code":404,
    "message":"Selected department not supported at the moment."
}

payment_processing = {
    "code":412,
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