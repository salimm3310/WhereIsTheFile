import streamlit as st
import hashlib
import re
from datetime import datetime
import pandas as pd
import urllib.parse
import plotly.express as px
from db_connection import execute_query

# =========================================================
# 1. إعدادات الصفحة والتصميم العام للهوية البصرية
# =========================================================
st.set_page_config(
    page_title="فين الملف؟ - Mohamed Salem OPS App",
    page_icon="📂",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    .main-title-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        margin-bottom: 5px;
    }
    .main-header {
        text-align: center;
        color: #1e3a8a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        margin-bottom: 2px;
        font-size: 32px;
    }
    .sub-header {
        text-align: center;
        color: #475569;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 6px;
        font-weight: bold;
        padding: 10px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
        color: white !important;
    }
    .chat-bubble-in {
        background-color: #ffffff;
        border-right: 4px solid #2563eb;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. دوال التشفير ومعالجة الحسابات
# =========================================================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def format_whatsapp_phone(raw_phone, default_country_code="20"):
    clean_phone = re.sub(r'[^\d]', '', str(raw_phone).strip())
    if clean_phone.startswith('00'):
        clean_phone = clean_phone[2:]
    if clean_phone.startswith('01') and len(clean_phone) == 11:
        clean_phone = default_country_code + clean_phone[1:]
    return clean_phone

# تهيئة الحسابات المسجلة وحالة الجلسة
if 'registered_users' not in st.session_state:
    st.session_state['registered_users'] = [
        {"user_id": 1, "full_name": "Mohamed Salem", "phone_number": "01212231815", "password_hash": make_hashes("123456"), "role_group": "Admin", "status": "Active"}
    ]

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =========================================================
# 3. الهيدر الرئيسي واللوجو المعدل
# =========================================================
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
with col_h2:
    col_img, col_txt = st.columns([1, 3])
    with col_img:
        try:
            st.image("logo.png", width=90)
        except:
            st.markdown("📂")
    with col_txt:
        st.markdown("<h1 style='color: #2563eb; margin:0;'>تطبيق فين الملف؟</h1>", unsafe_allow_html=True)

st.markdown("<h2 class='main-header'>Mohamed Salem OPS App</h2>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>نظام إدارة وتتبع الملفات</p>", unsafe_allow_html=True)

# =========================================================
# 4. شاشة تسجيل الدخول وإنشاء حساب جديد المحدثة
# =========================================================
if not st.session_state['logged_in']:
    tab_login, tab_register = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد"])

    with tab_login:
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            with st.form("login_form"):
                phone_input = st.text_input("رقم الهاتف المسجل:", placeholder="مثال: 01212231815")
                pass_input = st.text_input("كلمة المرور:", type="password")
                submit_login = st.form_submit_button("تسجيل الدخول")

                if submit_login:
                    user_found = None
                    for u in st.session_state['registered_users']:
                        if u['phone_number'].strip() == phone_input.strip() and check_hashes(pass_input.strip(), u['password_hash']):
                            user_found = u
                            break
                    
                    if user_found:
                        if user_found['status'] == "Active":
                            st.session_state['logged_in'] = True
                            st.session_state['user_info'] = user_found
                            st.success(f"✅ أهلاً بك يا {user_found['full_name']}! تم تسجيل الدخول بنجاح.")
                            st.rerun()
                        else:
                            st.warning("⏳ حسابك قيد المراجعة وبانتظار اعتماد مدير البرنامج (Mohamed Salem).")
                    else:
                        st.error("❌ بيانات الدخول غير صحيحة أو الحساب غير موجود.")

    with tab_register:
        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            st.markdown("### 📝 طلب إنشاء حساب جديد")
            st.info("💡 سيتم إرسال طلب الحساب لمدير البرنامج لتمكينه واعتماده قبل الدخول.")
            with st.form("register_form"):
                reg_name = st.text_input("الاسم الثلاثي:")
                reg_phone = st.text_input("رقم الهاتف (سيستخدم كاسم مستخدم):")
                reg_pass = st.text_input("كلمة المرور:", type="password")
                reg_role = st.selectbox("المجموعة المطلوب الانضمام لها:", ["مُشغّل (Operator)", "خدمة عملاء (CS)"])
                submit_reg = st.form_submit_button("إرسال طلب التسجيل")

                if submit_reg:
                    if reg_name.strip() != "" and reg_phone.strip() != "" and reg_pass.strip() != "":
                        new_u = {
                            "user_id": len(st.session_state['registered_users']) + 1,
                            "full_name": reg_name.strip(),
                            "phone_number": reg_phone.strip(),
                            "password_hash": make_hashes(reg_pass.strip()),
                            "role_group": "Operator" if "مُشغّل" in reg_role else "CS",
                            "status": "Pending"  # بانتظار الاعتماد من المدير
                        }
                        st.session_state['registered_users'].append(new_u)
                        st.success("🎉 تم إرسال طلب الحساب بنجاح! يرجى التواصل مع مدير البرنامج (Mohamed Salem) لاعتماده وتنشيطه.")
                    else:
                        st.error("⚠️ يرجى تعبئة كافة الحقول المطلوبة.")

else:
    user = st.session_state['user_info']
    col_u, col_l = st.columns([4, 1])
    with col_u:
        st.success(f"👤 الموظف: **{user['full_name']}** | المجموعة: **{user['role_group']}**")
    with col_l:
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    st.write("---")
    st.info("تم تسجيل الدخول بنجاح. نحن جاهزون للنتقل للوحة التالية حسب توجيهاتك.")