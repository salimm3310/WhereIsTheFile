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
# 2. دوال التشفير ومعالجة أرقام الهاتف
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

# تثبيت حسابك الرئيسي المعتمد ببياناتك الدقيقة
MAIN_ADMIN = {
    "user_id": 1,
    "full_name": "Mohamed Salem",
    "phone_number": "01212231815",
    "password_hash": make_hashes("691011"),
    "role_group": "Admin",
    "status": "Active"
}

if 'registered_users' not in st.session_state:
    st.session_state['registered_users'] = [MAIN_ADMIN]

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

if 'active_shipments' not in st.session_state:
    st.session_state['active_shipments'] = [
        {"id": 1, "file_num": "260862115", "company": "U.S.C", "bkg": "CFA0951367", "inv": "3A - 3B", "status": "Under Operation", "holded": 0, "h_reason": "", "last_up": "2026-09-18 10:00:00", "creator": "Mohamed Salem"},
        {"id": 2, "file_num": "260862116", "company": "CFA Global", "bkg": "CFA0951368", "inv": "104B", "status": "Waiting BL", "holded": 0, "h_reason": "", "last_up": "2026-09-18 11:30:00", "creator": "Mohamed Salem"},
        {"id": 3, "file_num": "260862117", "company": "Al-Salem Trading", "bkg": "CFA0951369", "inv": "88C", "status": "Ready to be invoiced", "holded": 0, "h_reason": "", "last_up": "2026-09-18 12:15:00", "creator": "Mohamed Salem"},
        {"id": 4, "file_num": "260862118", "company": "U.S.C", "bkg": "CFA0951370", "inv": "99A", "status": "Draft", "holded": 1, "h_reason": "في انتظار موافقة العميل", "last_up": "2026-09-18 09:00:00", "creator": "Mohamed Salem"}
    ]

if 'internal_messages' not in st.session_state:
    st.session_state['internal_messages'] = [
        {"sender": "النظام", "text": "مرحباً بك في نظام إدارة وتتبع الملفات.", "time": "10:00 AM"}
    ]

# =========================================================
# 3. الهيدر الرئيسي واللوجو
# =========================================================
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
with col_h2:
    st.markdown("<h1 style='text-align: center; color: #2563eb; margin:0;'>📂 تطبيق فين الملف؟</h1>", unsafe_allow_html=True)

st.markdown("<h2 class='main-header'>Mohamed Salem OPS App</h2>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>نظام إدارة وتتبع الملفات</p>", unsafe_allow_html=True)

# =========================================================
# 4. شاشة تسجيل الدخول وإنشاء حساب جديد المعتمدة
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
                    # التحقق أولاً من حساب المدير الرئيسي
                    if phone_input.strip() == MAIN_ADMIN["phone_number"] and check_hashes(pass_input.strip(), MAIN_ADMIN["password_hash"]):
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = MAIN_ADMIN
                        st.success(f"✅ أهلاً بك يا أستاذ {MAIN_ADMIN['full_name']}! تم تسجيل الدخول بنجاح.")
                        st.rerun()
                    else:
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
                reg_name = st.text_input("الاسم:")
                reg_phone = st.text_input("رقم الهاتف (سيستخدم كاسم مستخدم):")
                reg_pass = st.text_input("كلمة المرور:", type="password")
                
                # المجموعات الأربع المعتمدة حصراً
                reg_group = st.selectbox("المجموعة المطلوب الانضمام لها:", ["OPS", "Sys 1", "Sys 2", "Admin"])
                
                submit_reg = st.form_submit_button("إرسال طلب التسجيل")

                if submit_reg:
                    if reg_name.strip() != "" and reg_phone.strip() != "" and reg_pass.strip() != "":
                        new_u = {
                            "user_id": len(st.session_state['registered_users']) + 1,
                            "full_name": reg_name.strip(),
                            "phone_number": reg_phone.strip(),
                            "password_hash": make_hashes(reg_pass.strip()),
                            "role_group": reg_group,
                            "status": "Pending"
                        }
                        st.session_state['registered_users'].append(new_u)
                        st.success("🎉 تم إرسال طلب الحساب بنجاح! يرجى التواصل مع مدير البرنامج (Mohamed Salem) لاعتماده وتنشيطه.")
                    else:
                        st.error("⚠️ يرجى تعبئة كافة الحقول المطلوبة.")

# =========================================================
# 5. الواجهة الرئيسية بعد تسجيل الدخول
# =========================================================
else:
    user = st.session_state['user_info']
    
    col_u, col_l = st.columns([4, 1])
    with col_u:
        st.success(f"👤 المستخدم: **{user['full_name']}** | المجموعة الصلاحية: **{user['role_group']}**")
    with col_l:
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    st.write("---")

    menu = [
        "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)",
        "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)",
        "➕ إضافة شحنة جديدة (تفكيك الـ 11)",
        "💬 المراسلات والواتساب (Messaging & WhatsApp)",
        "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)",
        "📋 سجل الحالات والتدقيق (Status Logs)",
        "⚙️ لوحة التحكم الإدارية (Admin Panel)"
    ]
    choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

    # ---------------------------------------------------------
    # 1. التحليلات
    # ---------------------------------------------------------
    if choice == "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)":
        st.subheader("📈 لوحة التحليلات المتقدمة والشاملة (Comprehensive Analytics)")
        st.info("💡 هذه الشاشة جاهزة للمراجعة وتعديل بياناتها وفق توجيهاتك.")

    # ---------------------------------------------------------
    # 2. إدارة الحالات
    # ---------------------------------------------------------
    elif choice == "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)":
        st.subheader("🔄 شاشة إدارة الحالات وتتبع المهل الزمنية (SLA & Lifecycle)")
        st.info("💡 هذه الشاشة جاهزة للمراجعة وتعديل بياناتها وفق توجيهاتك.")

    # ---------------------------------------------------------
    # 3. إضافة شحنة
    # ---------------------------------------------------------
    elif choice == "➕ إضافة شحنة جديدة (تفكيك الـ 11)":
        st.subheader("📋 تفكيك السطر المرجعي وإدخال الشحنة (11 حقل)")
        st.info("💡 هذه الشاشة جاهزة للمراجعة وتعديل بياناتها وفق توجيهاتك.")

    # ---------------------------------------------------------
    # 4. المراسلات والواتساب
    # ---------------------------------------------------------
    elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
        st.subheader("💬 المراسلات الداخلية والتكامل مع WhatsApp")
        st.info("💡 هذه الشاشة جاهزة للمراجعة وتعديل بياناتها وفق توجيهاتك.")

    # ---------------------------------------------------------
    # 5. تقارير التقييم
    # ---------------------------------------------------------
    elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
        st.subheader("📊 تقارير تقييم الأداء والمكافآت والتأخيرات")
        st.info("💡 هذه الشاشة جاهزة للمراجعة وتعديل بياناتها وفق توجيهاتك.")

    # ---------------------------------------------------------
    # 6. سجل الحالات
    # ---------------------------------------------------------
    elif choice == "📋 سجل الحالات والتدقيق (Status Logs)":
        st.subheader("📋 سجل الحالات والتدقيق التاريخي (Status Logs & Audit Trail)")
        st.info("💡 هذه الشاشة جاهزة للمراجعة وتعديل بياناتها وفق توجيهاتك.")

    # ---------------------------------------------------------
    # 7. لوحة التحكم الإدارية (تتضمن اعتماد الحسابات والمجموعات الـ 4)
    # ---------------------------------------------------------
    elif choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
        st.subheader("⚙️ لوحة تحكم المدير وتعديل المهل SLA وتنشيط الحسابات (Mohamed Salem Control Panel)")

        tab_users_act, tab_sla_cfg = st.tabs(["👥 اعتماد وتنشيط حسابات الموظفين", "⏱️ إعدادات المهل SLA"])

        with tab_users_act:
            st.markdown("### 👥 طلبات الحسابات بانتظار اعتماد المدير")
            pending_list = [u for u in st.session_state['registered_users'] if u['status'] == "Pending"]
            
            if len(pending_list) > 0:
                for p_user in pending_list:
                    c_u1, c_u2, c_u3, c_u4 = st.columns([2, 2, 2, 2])
                    c_u1.write(f"**الاسم:** {p_user['full_name']}")
                    c_u2.write(f"**الهاتف:** {p_user['phone_number']}")
                    c_u3.write(f"**المجموعة المطلوب:** {p_user['role_group']}")
                    
                    if c_u4.button(f"✅ اعتماد وتفعيل الحساب", key=f"act_{p_user['user_id']}"):
                        p_user['status'] = "Active"
                        st.success(f"🎉 تم اعتماد وتفعيل حساب {p_user['full_name']} بالمجموعة ({p_user['role_group']}) بنجاح!")
                        st.rerun()
            else:
                st.success("✅ لا توجد طلبات حسابات جديدة بانتظار الاعتماد حالياً.")

            st.write("---")
            st.markdown("### 📋 قائمة الحسابات المفعلة بالنظام")
            active_df = pd.DataFrame([u for u in st.session_state['registered_users'] if u['status'] == "Active"])
            if not active_df.empty:
                st.dataframe(active_df[["full_name", "phone_number", "role_group", "status"]], use_container_width=True)

        with tab_sla_cfg:
            st.markdown("### ⏱️ إعدادات المهل الزمنية والتوقيتات المتغيرة")
            st.info("جاهزة للتعديل حسب توجيهاتك.")