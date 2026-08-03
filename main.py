import requests

SERVICE_KEY = ""


def main(biz_num_list: list[str]) -> list[dict]:
    url = f"https:///api.odcloud.kr/api/nts-businessman/v1/status?serviceKey={SERVICE_KEY}"
    body = {"b_no": biz_num_list}

    res = requests.post(url, json=body)
    """
    {
      "status_code": "OK",
      "match_cnt": 1,
      "request_cnt": 1,
      "data": [
        {
          "b_no": "0000000000",
          "b_stt": "계속사업자",
          "b_stt_cd": "01",
          "tax_type": "부가가치세 일반과세자",
          "tax_type_cd": "01",
          "end_dt": "20000101",
          "utcc_yn": "Y",
          "tax_type_change_dt": "20000101",
          "invoice_apply_dt": "20000101",
          "rbf_tax_type": "부가가치세 일반과세자",
          "rbf_tax_type_cd": "01"
        }
      ]
    }
    """
    if not res.ok:
        raise Exception("API request failed")

    result = res.json()
    if result["status_code"] != "OK":
        raise Exception("API request failed")

    data = result["data"]
    return [
        {"biz_num": d["b_no"], "status": d["b_stt"], "tax_type": d["tax_type"]}
        for d in data
    ]


if __name__ == "__main__":
    print(main(["8445300712"]))
