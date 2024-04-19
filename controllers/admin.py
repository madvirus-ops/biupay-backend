import sys
sys.path.append("./")
from controllers.paystack import headers,baseurl
import requests
from controllers import responses as r



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


            