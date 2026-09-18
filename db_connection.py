import requests
import json
import streamlit as st

# =========================================================
# بيانات الاتصال الخاصة بـ Supabase REST API
# =========================================================
SUPABASE_URL = "https://xmhmwtbnbdmrcvyvflrh.supabase.co"
SUPABASE_KEY = "sb_secret_crCHdfqhE35AaURGxuIbqQ_l-Jp7hQC"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =========================================================
# الدالة الشاملة لتنفيذ الاستعلامات عبر HTTP REST API
# =========================================================
def execute_query(query, params=None, fetch=False):
    try:
        query_upper = query.strip().upper()

        # -------------------------------------------------
        # 1. استعلامات القراءة (SELECT)
        # -------------------------------------------------
        if fetch:
            table_name = query.split("FROM")[1].split()[0].strip()
            url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*"

            # معالجة شرط WHERE لـ phone_number أو غيره
            if "WHERE" in query_upper and params:
                where_clause = query.split("WHERE")[1].split()[0].strip()
                param_val = params[0]
                url += f"&{where_clause}=eq.{param_val}"

            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                if data:
                    columns = list(data[0].keys())
                    rows = [list(item.values()) for item in data]
                    return columns, rows
                return [], []
            else:
                st.error(f"❌ خطأ في جلب البيانات: {response.text}")
                return None

        # -------------------------------------------------
        # 2. استعلامات الإضافة والتحديث (INSERT / UPDATE)
        # -------------------------------------------------
        else:
            if "INSERT INTO" in query_upper:
                table_name = query.split("INTO")[1].split("(")[0].strip()
                url = f"{SUPABASE_URL}/rest/v1/{table_name}"

                fields_str = query.split("(")[1].split(")")[0]
                fields = [f.strip() for f in fields_str.split(",")]

                if params and len(fields) == len(params):
                    payload = dict(zip(fields, params))
                    response = requests.post(url, headers=HEADERS, json=payload)
                    return response.status_code in [200, 201]

            elif "UPDATE" in query_upper:
                table_name = query.split("SET")[0].replace("UPDATE", "").replace("update", "").strip()
                url = f"{SUPABASE_URL}/rest/v1/{table_name}"

                if "WHERE" in query_upper and params:
                    where_field = query.split("WHERE")[1].split("=")[0].strip()
                    where_val = params[-1]
                    url += f"?{where_field}=eq.{where_val}"

                    set_str = query.split("SET")[1].split("WHERE")[0].strip()
                    set_fields = [s.split("=")[0].strip() for s in set_str.split(",")]
                    set_vals = params[:-1]
                    payload = dict(zip(set_fields, set_vals))

                    response = requests.patch(url, headers=HEADERS, json=payload)
                    return response.status_code in [200, 204]

            return True

    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بالسحابة: {e}")
        return None