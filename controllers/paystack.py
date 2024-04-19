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
)
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
import json

baseurl = get_env("PAYSTACK_URL")
secret_key = get_env("PAYSTACK_SECRET_KEY")

headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}


def initialiaze_payment(
    email: str,
    full_name: str,
    phone_number: str,
    department: str,
    level: str,
    matric_number: str,
    session: str,
    db: Session,
):
    try:
        dept = (
            db.query(Departments)
            .filter(Departments.code == department.strip().lower())
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
                department=department.strip().lower(),
                level=level.strip().lower(),
                matric_number=matric_number.strip().lower(),
            )
            db.commit(user)
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
        amount = int(dept.dues_amount + dept.payment_fees)
        payload = {
            "email": user.email,
            "amount": str(amount * 100),
            "channels": ["bank_transfer", "ussd", "bank"],
            "metadata": {
                "session": session.strip().lower(),
            },
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
                    payer_id=user.email,
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
            user = (
                db.query(Users)
                .filter(or_(Users.email == email, Users.email == check.payer_email))
                .first()
            )
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
        else:
            print("Unhandled event data", data["event"])
            print("Event data", data)
    except Exception as e:
        print(e.args)
        return r.error_occured


def check_payment_status(matric_number: str, session: str, db: Session):
    try:
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

