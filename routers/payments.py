import sys

sys.path.append("./")
from connections.database import get_db
from controllers.paystack import (
    handle_webhooks_transactions,
    check_payment_status,
    initialiaze_payment,
    get_all_departmenst,
    secret_key
)
from fastapi import APIRouter, Response, Request, Depends,HTTPException
from sqlalchemy.orm import Session
from connections.schemas import InitPayment
import json
import hashlib
import hmac

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.get("/departments")
async def get_all__departments(db: Session = Depends(get_db)):
    return get_all_departmenst(db)


@router.post("/initialize")
async def init_payments(
    body: InitPayment, response: Response, db: Session = Depends(get_db)
):
    """
        `department_code` is the `code` you get from the response in the endpoint above this\n
        `session` is in this format `2022/2023`
    
    """
    result = initialiaze_payment(
        body.email,
        body.full_name,
        body.phone_number,
        body.department_code,
        body.level,
        body.matric_number,
        body.session,
        db,
    )
    response.status_code = result["code"]
    return result



@router.get("/status")
async def check_status(
    matric_number:str,
    session:str,
    response:Response,
    db:Session = Depends(get_db)
):
    result = check_payment_status(matric_number,session,db)
    response.status_code = result['code']
    return result


@router.post("/completed",include_in_schema=False)
async def handle_webhook_(request: Request, db: Session = Depends(get_db)):
    """
    `this is not your business, avoid it`
    """
    key = secret_key
    output = await request.body()
    byte_key = bytearray(key, "utf-8")

    hashed_key = hmac.new(byte_key, msg=output, digestmod=hashlib.sha512).hexdigest()
    requested_header = request.headers.get("x-paystack-signature")

    if hashed_key != requested_header:
        print("Not Valid?")
        raise HTTPException(401,"Invalid webhook")
    else:
        json_output = json.loads(output)
        result = await handle_webhooks_transactions(json_output, db)
        return {"status":"success"}