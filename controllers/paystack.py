import sys

sys.path.append("./")
from controllers import responses as r
import requests
from connections.models import (
    Users,
    Transactions,
    Departments,
    get_env,
    PaystackWebhooks,
    tz,
    OutgoingPayment,
)
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
import json
import re

baseurl = get_env("PAYSTACK_URL")
secret_key = get_env("PAYSTACK_SECRET_KEY")

headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}


def validate_session(session):
    pattern = r"^\d{4}/\d{4}$"
    return re.match(pattern, session)


def initialiaze_payment(
    email: str,
    full_name: str,
    phone_number: str,
    department_code: str,
    level: str,
    matric_number: str,
    session: str,
    db: Session,
):
    try:
        if not validate_session(session):
            return r.invalid_session

        dept = (
            db.query(Departments)
            .filter(Departments.code == department_code.strip().lower())
            .first()
        )
        if not dept:
            return r.dept_not_found

        user = db.query(Users).filter(Users.email == email.strip().lower()).first()
        if not user:
            user = Users(
                email=email.strip().lower(),
                phone_number=phone_number.strip().lower(),
                full_name=full_name.strip().lower(),
                department=department_code.strip().lower(),
                level=level.strip().lower(),
                matric_number=matric_number.strip().lower(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        exist = (
            db.query(Transactions)
            .filter(
                Transactions.payer_email == user.email,
                Transactions.session == session.strip().lower(),
                Transactions.payment_status.not_in(["completed"]),
            )
            .first()
        )
        if exist:
            return r.payment_processing

        url = baseurl + "/transaction/initialize"
        fee = (dept.payment_fees / 100) * dept.dues_amount
        amount = int(dept.dues_amount + fee)
        payload = {
            "email": user.email,
            "amount": str(amount * 100),
            "channels": ["bank_transfer", "ussd", "bank"],
            "metadata": {"session": session.strip().lower(), "department": dept.code},
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()["data"]
            reference = data["reference"]
            redirect_url = data["authorization_url"]
            new = Transactions(
                payer_email=user.email,
                status="pending",  # pending or processed when the webhook neva come
                payment_status="processing",  # completed or processing.
                department_code=dept.code,
                amount=amount,
                session=session.strip().lower(),
                created_at=datetime.now(tz),
                updated_at=datetime.now(tz),
                payment_reference=reference,
                level=level,
            )
            db.add(new)
            db.add(
                PaystackWebhooks(
                    status="pending",
                    payer_email=user.email,
                    reference=reference,
                    body=json.dumps(data),
                )
            )
            user.level = level if level != user.level else user.level
            db.commit()
            return {
                "code": 200,
                "message": "proceeed to make payment",
                "data": {"reference": reference, "url": redirect_url},
            }
        else:
            print(response.text)
            return r.error_occured
    except Exception as e:
        print(e.args)
        return r.error_occured


def handle_webhooks_transactions(data: dict, db: Session):
    try:
        email = data["data"]["customer"]["email"]
        reference = data["data"]["reference"]
        check = (
            db.query(PaystackWebhooks)
            .filter(PaystackWebhooks.reference == reference)
            .first()
        )
        print(data)

        if check is not None and check.status == "processed":
            return True

        check = PaystackWebhooks(
            status="pending",
            reference=reference,
            body=json.dumps(data),
            payer_email=email,
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        if data["event"] == "charge.success":
            amount = int(data["data"]["amount"]) / 100
            session = data["data"]["metadata"]["session"]
            dept = data["data"]["metadata"]["department"]
            user = (
                db.query(Users)
                .filter(or_(Users.email == email, Users.email == check.payer_email))
                .first()
            )
            depet = db.query(Departments).filter(Departments.code == dept).first()
            transaction = (
                db.query(Transactions)
                .filter(
                    Transactions.payer_email == user.email,
                    Transactions.session == session,
                )
                .first()
            )
            transaction.status = "processed"
            transaction.payment_status = "completed"
            transaction.updated_at = datetime.now(tz)
            db.commit()
            check.status = "processed"
            check.body = json.dumps(data)
            # TODO send email to user or stuffs like that
            transs = transfer_to_admin(
                user.email,
                reference,
                depet.bank_code,
                depet.account_number,
                f"{user.matric_number}=={user.full_name}=={user.email}",
                depet.dues_amount,
                db,
            )
            print(transs)
        else:
            print("Unhandled event data", data["event"])
            print("Event data", data)
    except Exception as e:
        print(e.args)
        return r.error_occured


def check_payment_status(matric_number: str, session: str, db: Session):
    try:
        if not validate_session(session):
            return r.invalid_session
        matric_number = matric_number.strip().lower()
        session = session.strip().lower()
        user = (
            db.query(Users)
            .filter(Users.matric_number == matric_number.strip().lower())
            .first()
        )
        if not user:
            return r.payment_not_found
        payment = (
            db.query(Transactions)
            .filter(
                Transactions.payer_email == user.email, Transactions.session == session
            )
            .first()
        )
        if not payment:
            return r.payment_session_not_found
        dept = (
            db.query(Departments)
            .filter(Departments.code == payment.department_code)
            .first()
        )
        return {
            "code": 200,
            "message": "records found",
            "data": {
                "amount": payment.amount,
                "status": payment.status,
                "department": dept.name,
                "receipient": user.full_name,
                "matric_number": user.matric_number,
                "level": payment.level,
                "phone_number": user.phone_number,
                "email": user.email,
                "date": payment.created_at,
            },
        }
    except Exception as e:
        print(e.args)
        return r.error_occured


def get_all_departmenst(db: Session):
    return db.query(Departments).all()


def ValidateAccount(bank_code: str, account_number: str):
    try:
        url = (
            baseurl
            + f"/bank/resolve?account_number={account_number}&bank_code={bank_code}"
        )
        print(url)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()["data"]
            return {
                "success": True,
                "code": 200,
                "message": "Account fetched",
                "data": {
                    "account_number": account_number,
                    "account_name": data["account_name"],
                    "beneficiaryBankCode": bank_code,
                },
            }
        print(response.json())
        return r.error_occured
    except Exception as e:
        print(e.args)
        return r.error_occured


def CreateTransferReceipient(
    account_number,
    bank_code,
):
    try:
        resolve = ValidateAccount(bank_code, account_number)
        if resolve["code"] != 200:
            return r.error_occured
        account_name = resolve["data"]["account_name"]

        url = f"{baseurl}/transferrecipient"
        payload = {
            "type": "nuban",
            "name": account_name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN",
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code <= 300:
            data = response.json()["data"]
            code = data["recipient_code"]
            return {"code": 200, "send_code": code}
        print(response.status_code, response.json())
        return {"code": 400}
    except Exception as e:
        print(e.args)
        return r.error_occured


def transfer_to_admin(
    payer_email: str,
    reference: str,
    bank_code: str,
    account_number: str,
    narration: str,
    amount: int,
    db: Session,
):
    try:
        check = (
            db.query(OutgoingPayment)
            .filter(
                OutgoingPayment.reference == reference,
                OutgoingPayment.payer_email == payer_email,
            )
            .first()
        )

        if check and check.status == "processed":
            return r.payment_processing

        ress = CreateTransferReceipient(account_number, bank_code)
        if ress["code"] == 400:
            return r.service_unavailable
        payload = {
            "source": "balance",
            "reason": narration,
            "amount": int(float(amount)) * 100,
            "recipient": ress["send_code"],
        }
        url = baseurl + "/transfer"

        check = OutgoingPayment(
            status="pending",
            reference=reference,
            body=json.dumps(payload),
            payer_email=payer_email,
        )
        db.add(check)
        db.commit()
        db.refresh(check)
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code <= 300:
            data = response.json()["data"]
            print(data)
            ses_id = data["transfer_code"]
            if data["status"] == "pending":
                check.status = "processed"
                check.updated_at = datetime.now(tz)
                check.body = json.dumps(data)
                db.commit()
                return {"code":200,"message":data}
            return {"code":400,"message":data}
        print(response.text)
        return {"code":400,"message":"transfer failed"}
    except Exception as e:
        print(e.args)
        return r.error_occured
