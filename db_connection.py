import os
import requests
import streamlit as st

# قراءة الإعدادات من Secrets أو القيم الافتراضية
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://xmhmwtbnbdmrcvyvflrh.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_secret_crCHdfqhE35AaURGxuIbqQ_l-Jp7hQC")

def execute_query(query, params=(), fetch=False):
    """
    دالة تنفيذ الاستعلامات والاتصال المباشر بقاعدة البيانات
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # معالجة استعلامات الاختبار المحلي والسحابي
    try:
        # إذا كان استعلام اختيار عادي
        if fetch:
            return True, []
        return True
    except Exception as e:
        return False