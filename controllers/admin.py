import sys

sys.path.append("./")
from controllers.paystack import headers, baseurl
import requests
from controllers import responses as r
from connections.models import (
    Departments,
    get_env,
)
from connections.schemas import DepartmentsIN
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
import json
import re



def listAllBanks():
    try:
        url = baseurl + "/bank"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()["data"]
            resp = []
            for one in data:
                resp.append({"bankCode": one["code"], "bankName": one["name"]})

            return {
                "code": 200,
                "message": "bank fetched",
                "success": True,
                "data": resp,
            }
        return r.error_occured
    except Exception as e:
        print(e.args)
        return r.error_occured


def edit_department(body: DepartmentsIN, db: Session):
    try:
        department = db.query(Departments).filter(Departments.id == body.id).first()
        if not department:
            return r.dept_not_found
        body_data = body.model_dump(exclude_unset=True)
        for key, value in body_data.items():
            if isinstance(key, str):
                val = val.lower()
            else:
                val = value
                
            setattr(department, key, value)

        db.add(department)
        db.commit()
        return r.updated

    except Exception as e:
        print(e.args)
        return r.error_occured
