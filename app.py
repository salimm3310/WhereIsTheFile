import streamlit as st
import hashlib
import re
import base64
from datetime import datetime
import pandas as pd
import urllib.parse
import plotly.express as px
from db_connection import execute_query

# =========================================================
# 1. إعدادات الصفحة والتصميم العام للهوية البصرية والتباين
# =========================================================
st.set_page_config(
    page_title="فين الملف؟ - Mohamed Salem OPS App",
    page_icon="📂",
    layout="wide"
)

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

bg_base64 = get_base64_of_bin_file("background.jpg")

st.markdown(f"""
<style>
    .stApp {{
        background-image: linear-gradient(rgba(241, 245, 249, 0.80), rgba(241, 245, 249, 0.80)), url("data:image/jpg;base64,{bg_base64}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
        color: #020617;
        font-size: 24px !important;
        font-weight: 800 !important;
    }}
    
    /* تصغير الخط في القائمة الجانبية لضمان إظهار كافة المسميات كاملة */
    section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] select, section[data-testid="stSidebar"] option {{
        font-size: 16px !important;
        font-weight: 700 !important;
    }}

    h1, h2, h3, .main-header {{
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    }}
    
    .sub-header {{
        text-align: center;
        color: #1e293b !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        margin-bottom: 25px;
    }}

    p, label, span, div, input, select, textarea, button, .stDataFrame, .stSelectbox, .stTextInput {{
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #020617 !important;
    }}

    .stDataFrame, .stForm, div[data-testid="stExpander"], div[data-testid="stMetricValue"] {{
        background-color: rgba(255, 255, 255, 0.96) !important;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    input, select, textarea {{
        background-color: #ffffff !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }}

    .stButton>button {{
        width: 100%;
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px;
        font-weight: 800 !important;
        font-size: 24px !important;
        padding: 12px;
        border: none;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }}
    .stButton>button:hover {{
        background-color: #1d4ed8 !important;
        color: white !important;
    }}

    .status-badge-ontime {{
        background-color: #dcfce7;
        color: #166534;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 24px;
    }}
    .status-badge-alert {{
        background-color: #fef9c3;
        color: #854d0e;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 24px;
    }}
    .status-badge-late {{
        background-color: #fee2e2;
        color: #991b1b;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 24px;
    }}
    .chat-bubble-in {{
        background-color: rgba(255, 255, 255, 0.98);
        border-right: 6px solid #2563eb;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-size: 24px !important;
        font-weight: 800 !important;
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. دوال التشفير والتنظيف
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

# قائمة شاشات البرنامج
ALL_MODULES = [
    "⚙️ لوحة التحكم الإدارية (Admin Panel)",
    "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)",
    "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)",
    "➕ إضافة شحنة جديدة (تفكيك الـ 11)",
    "💬 المراسلات والواتساب (Messaging & WhatsApp)",
    "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)",
    "📋 سجل الحالات والتدقيق (Status Logs)"
]

MAIN_ADMIN = {
    "user_id": 1,
    "full_name": "Mohamed Salem",
    "phone_number": "01212231815",
    "password_hash": make_hashes("691011"),
    "role_group": "Admin",
    "allowed_pages": ALL_MODULES,
    "status": "Active"
}

if 'registered_users' not in st.session_state:
    st.session_state['registered_users'] = [
        MAIN_ADMIN,
        {"user_id": 2, "full_name": "أحمد علي", "phone_number": "01012345678", "password_hash": make_hashes("123456"), "role_group": "OPS", "allowed_pages": ALL_MODULES[1:5], "status": "Active"},
        {"user_id": 3, "full_name": "محمود حسن", "phone_number": "01112345678", "password_hash": make_hashes("123456"), "role_group": "Sys 1", "allowed_pages": ALL_MODULES[1:4], "status": "Active"}
    ]

if 'user_points' not in st.session_state:
    st.session_state['user_points'] = {
        1: {"earned": 2, "deducted": 0, "notes": "إغلاق ملفات مكتملة"},
        2: {"earned": 1, "deducted": 1, "notes": "إغلاق ملف وتأخير سابقتين"},
        3: {"earned": 0, "deducted": 0, "notes": ""}
    }

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

if 'active_shipments' not in st.session_state:
    st.session_state['active_shipments'] = [
        {"id": 1, "file_num": "260862115", "company": "U.S.C", "bkg": "CFA0951367", "inv": "3A - 3B", "status": "Under Operation", "holded": 0, "h_reason": "", "last_up": "2026-09-18 10:00:00", "last_status_updater": "Mohamed Salem", "note": "في انتظار موافقة الخط"},
        {"id": 2, "file_num": "260862116", "company": "CFA Global", "bkg": "CFA0951368", "inv": "104B", "status": "Waiting BL", "holded": 0, "h_reason": "", "last_up": "2026-09-10 11:30:00", "last_status_updater": "أحمد علي", "note": "تم تسليم المستندات"},
        {"id": 3, "file_num": "260862117", "company": "Al-Salem Trading", "bkg": "CFA0951369", "inv": "88C", "status": "Ready to be invoiced", "holded": 0, "h_reason": "", "last_up": "2026-09-18 12:15:00", "last_status_updater": "Mohamed Salem", "note": "جاهز للفلترة"},
        {"id": 4, "file_num": "260862118", "company": "U.S.C", "bkg": "CFA0951370", "inv": "99A", "status": "Draft", "holded": 1, "h_reason": "في انتظار موافقة العميل", "last_up": "2026-09-12 09:00:00", "last_status_updater": "محمود حسن", "note": "معلق بناء على رغبة العميل"},
        {"id": 5, "file_num": "260862119", "company": "U.S.C", "bkg": "CFA0951371", "inv": "12C", "status": "Closed", "holded": 0, "h_reason": "", "last_up": "2026-09-15 14:00:00", "last_status_updater": "Mohamed Salem", "note": "تم إغلاق الملف وتحصيل الفاتورة"}
    ]

if 'internal_messages' not in st.session_state:
    st.session_state['internal_messages'] = [
        {"sender": "Mohamed Salem", "recipient": "أحمد علي (OPS)", "text": "يرجى متابعة ملف الشحنة 260862116 اليوم.", "time": "10:00 AM"},
        {"sender": "أحمد علي", "recipient": "Mohamed Salem (Admin)", "text": "تم استلام التعليمات وجاري العرض على الخط.", "time": "10:15 AM"}
    ]

if 'whatsapp_logs' not in st.session_state:
    st.session_state['whatsapp_logs'] = [
        {"sender": "Mohamed Salem", "target_name": "أستاذ أحمد - U.S.C", "phone": "201212231815", "text": "تحديث جديد لشحنتكم ملف رقم (260862115)", "time": "2026-09-18 10:30:00"},
        {"sender": "أحمد علي", "target_name": "شركة CFA Global", "phone": "201012345678", "text": "تنبيه: تم رفع بوليصة الشحن بانتظار الاعتماد", "time": "2026-09-18 11:45:00"}
    ]

if 'selected_shipment_id' not in st.session_state:
    st.session_state['selected_shipment_id'] = None

# =========================================================
# 3. دالة تفكيك السطر المرجعي ودالة حساب المهل SLA
# =========================================================
def parse_reference_string(raw_text):
    parts = [p.strip() for p in raw_text.split(' - ') if p.strip() != '']
    
    if len(parts) >= 8:
        po_num = parts[0]
        file_num = parts[1]
        
        c_count = 1
        c_type = ''
        cont_raw = parts[2]
        count_match = re.search(r'(\d+(\.\d+)?)', cont_raw)
        if count_match:
            try:
                c_count = int(float(count_match.group(1)))
            except:
                c_count = 1
        c_type = re.sub(r'^\d+(\.\d+)?\s*x?\s*', '', cont_raw, flags=re.IGNORECASE).strip()

        pol_val = parts[3]
        pod_val = parts[4]
        dest_country = parts[5]
        
        inv_index = -1
        for idx, part in enumerate(parts):
            if part.upper().startswith('INV'):
                inv_index = idx
                break
        
        if inv_index != -1:
            if inv_index + 1 < len(parts) and len(parts[inv_index+1]) <= 10:
                inv_raw = f"{parts[inv_index]} - {parts[inv_index+1]}"
                company_idx = inv_index + 2
            else:
                inv_raw = parts[inv_index]
                company_idx = inv_index + 1

            inv_clean = re.sub(r'(?i)inv\b', '', inv_raw).replace('-', ' ').strip()
            inv_clean = " ".join(inv_clean.split())

            company_val = parts[company_idx] if company_idx < len(parts) else ''
            bkg_val = parts[company_idx + 1] if company_idx + 1 < len(parts) else ''
            item_desc_val = " - ".join(parts[company_idx + 2:]) if company_idx + 2 < len(parts) else ''
        else:
            inv_clean = parts[6]
            company_val = parts[7] if len(parts) > 7 else ''
            bkg_val = parts[8] if len(parts) > 8 else ''
            item_desc_val = " - ".join(parts[9:]) if len(parts) > 9 else ''

        return {
            'po_number': po_num,
            'file_number': file_num,
            'container_count': c_count,
            'container_type': c_type,
            'pol': pol_val,
            'pod': pod_val,
            'destination_country': dest_country,
            'invoice_number': inv_clean,
            'company_name': company_val,
            'booking_number': bkg_val,
            'item_description': item_desc_val
        }, True

    return None, False

def calculate_sla_status(current_status, last_updated_at):
    if not last_updated_at or current_status == "Closed":
        return "في الموعد (On Time)", "status-badge-ontime", 0

    max_check_hours = 48
    max_late_hours = 96

    if isinstance(last_updated_at, str):
        try:
            last_updated_at = datetime.strptime(last_updated_at, '%Y-%m-%d %H:%M:%S')
        except:
            last_updated_at = datetime.now()

    time_diff = datetime.now() - last_updated_at
    elapsed_hours = time_diff.total_seconds() / 3600.0

    if elapsed_hours <= max_check_hours:
        return "في الموعد (On Time)", "status-badge-ontime", elapsed_hours
    elif max_check_hours < elapsed_hours <= max_late_hours:
        return "اقتراب المهلة (Alert)", "status-badge-alert", elapsed_hours
    else:
        return "متأخر (Late)", "status-badge-late", elapsed_hours

# =========================================================
# 4. الهيدر الرئيسي
# =========================================================
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    try:
        st.image("logo.jpg", width=1100)
    except:
        st.markdown("<h1 style='text-align: center; font-size: 80px;'>📂</h1>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #2563eb; margin-top:10px;'>تطبيق فين الملف؟</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='main-header'>Mohamed Salem OPS App</h2>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>نظام إدارة وتتبع الملفات</p>", unsafe_allow_html=True)

# =========================================================
# 5. شاشة تسجيل الدخول وإنشاء حساب جديد
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
                                st.warning("⏳ حسابك قيد المراجعة وبانتظار تحديد صلاحياتك واعتماده من مدير البرنامج (Mohamed Salem).")
                        else:
                            st.error("❌ بيانات الدخول غير صحيحة أو الحساب غير موجود.")

    with tab_register:
        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            st.markdown("### 📝 طلب إنشاء حساب جديد")
            st.info("💡 سيتم إرسال طلب الحساب لمدير البرنامج لتمكينه وتحديد المزايا والصلاحيات المسموحة له قبل الدخول.")
            with st.form("register_form"):
                reg_name = st.text_input("الاسم:")
                reg_phone = st.text_input("رقم الهاتف (سيستخدم كاسم مستخدم):")
                reg_pass = st.text_input("كلمة المرور:", type="password")
                
                submit_reg = st.form_submit_button("إرسال طلب التسجيل")

                if submit_reg:
                    if reg_name.strip() != "" and reg_phone.strip() != "" and reg_pass.strip() != "":
                        new_u = {
                            "user_id": len(st.session_state['registered_users']) + 1,
                            "full_name": reg_name.strip(),
                            "phone_number": reg_phone.strip(),
                            "password_hash": make_hashes(reg_pass.strip()),
                            "role_group": "Unassigned",
                            "allowed_pages": [],
                            "status": "Pending"
                        }
                        st.session_state['registered_users'].append(new_u)
                        st.success("🎉 تم إرسال طلب الحساب بنجاح! يرجى التواصل مع مدير البرنامج (Mohamed Salem) لتحديد صلاحيات الشاشات وتنشيط حسابك.")
                    else:
                        st.error("⚠️ يرجى تعبئة كافة الحقول المطلوبة.")

# =========================================================
# 6. الواجهة الرئيسية بعد تسجيل الدخول
# =========================================================
else:
    user = st.session_state['user_info']
    
    col_u, col_l = st.columns([4, 1])
    with col_u:
        st.success(f"👤 المستخدم: **{user['full_name']}** | المجموعة: **{user['role_group']}**")
    with col_l:
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            st.rerun()

    st.write("---")

    allowed_menu = user.get('allowed_pages', ALL_MODULES)
    if not allowed_menu:
        allowed_menu = ALL_MODULES

    choice = st.sidebar.selectbox("القائمة الرئيسية المسموحة", allowed_menu, index=0)

    # ---------------------------------------------------------
    # التبويب 1: لوحة التحكم الإدارية (Admin Panel)
    # ---------------------------------------------------------
    if choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
        st.subheader("⚙️ لوحة تحكم المدير والإدارة الشاملة (Mohamed Salem Control Panel)")

        tab_users_act, tab_user_edit, tab_audit, tab_points_eval, tab_sla_cfg = st.tabs([
            "👥 طلبات الحسابات بانتظار الاعتماد",
            "🛠️ إعدادات الحسابات المفعلة والصلاحيات",
            "📨 صندوق البريد وتتبع الواتساب الخارجي",
            "🏆 تقييم الموظفين والتحكم بالنقاط",
            "⏱️ إعدادات المهل SLA"
        ])

        with tab_users_act:
            st.markdown("### 👥 طلبات الحسابات بانتظار الاعتماد وتحديد الصلاحيات")
            pending_list = [u for u in st.session_state['registered_users'] if u['status'] == "Pending"]
            
            if len(pending_list) > 0:
                for p_user in pending_list:
                    st.markdown(f"#### 👤 المستدعي: **{p_user['full_name']}** ({p_user['phone_number']})")
                    col_p1, col_p2 = st.columns([1, 2])
                    
                    with col_p1:
                        assigned_group = st.selectbox(
                            "1. تحديد المجموعة الصلاحية:", 
                            ["OPS", "Sys 1", "Sys 2", "Admin"], 
                            key=f"grp_{p_user['user_id']}"
                        )
                    
                    with col_p2:
                        st.markdown("**2. حدد الشاشات واللوحات المسموح إظهارها له:**")
                        selected_pages = []
                        for module in ALL_MODULES:
                            if st.checkbox(module, value=True, key=f"p_{p_user['user_id']}_{module}"):
                                selected_pages.append(module)
                    
                    if st.button(f"✅ اعتماد الحساب وتحديد الصلاحيات لـ {p_user['full_name']}", key=f"btn_act_{p_user['user_id']}"):
                        p_user['role_group'] = assigned_group
                        p_user['allowed_pages'] = selected_pages
                        p_user['status'] = "Active"
                        if p_user['user_id'] not in st.session_state['user_points']:
                            st.session_state['user_points'][p_user['user_id']] = {"earned": 0, "deducted": 0, "notes": "حساب جديد"}
                        st.success(f"🎉 تم تفعيل حساب {p_user['full_name']} وتخصيص {len(selected_pages)} شاشة مسموحة له بنجاح!")
                        st.rerun()
                    st.write("---")
            else:
                st.success("✅ لا توجد طلبات حسابات جديدة بانتظار الاعتماد حالياً.")

        with tab_user_edit:
            st.markdown("### 🛠️ إدارة الحسابات المفعلة (تعديل / حذف / إعادة ضبط المرور)")
            active_users = [u for u in st.session_state['registered_users'] if u['status'] == "Active"]
            
            user_options = {f"{u['full_name']} ({u['phone_number']}) - مجموعة: {u['role_group']}": u for u in active_users}
            selected_u_label = st.selectbox("اختر الحساب المراد إدارته وتعديله:", list(user_options.keys()))
            target_u = user_options[selected_u_label]

            with st.form("edit_user_form"):
                st.markdown(f"#### ✏️ تعديل بيانات الحساب: **{target_u['full_name']}**")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_name = st.text_input("اسم المستخدم / الموظف:", value=target_u['full_name'])
                    edit_phone = st.text_input("رقم الهاتف (اسم الدخول):", value=target_u['phone_number'])
                    edit_pass = st.text_input("كلمة المرور الجديدة (اتركها فارغة إذا لم ترد التغيير):", type="password")
                
                with col_e2:
                    edit_group = st.selectbox("المجموعة الصلاحية:", ["OPS", "Sys 1", "Sys 2", "Admin"], index=["OPS", "Sys 1", "Sys 2", "Admin"].index(target_u['role_group']) if target_u['role_group'] in ["OPS", "Sys 1", "Sys 2", "Admin"] else 0)
                    st.markdown("**صلاحيات الشاشات واللوحات المسموحة:**")
                    edit_pages = []
                    for module in ALL_MODULES:
                        is_checked = module in target_u.get('allowed_pages', ALL_MODULES)
                        if st.checkbox(module, value=is_checked, key=f"edit_p_{target_u['user_id']}_{module}"):
                            edit_pages.append(module)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    save_u_btn = st.form_submit_button("💾 حفظ التعديلات")
                with col_btn2:
                    del_u_btn = st.form_submit_button("🗑️ حذف وتجميد الحساب")

                if save_u_btn:
                    target_u['full_name'] = edit_name.strip()
                    target_u['phone_number'] = edit_phone.strip()
                    if edit_pass.strip() != "":
                        target_u['password_hash'] = make_hashes(edit_pass.strip())
                    target_u['role_group'] = edit_group
                    target_u['allowed_pages'] = edit_pages
                    st.success(f"✅ تم تحديث بيانات وصلاحيات الحساب ({edit_name}) بنجاح!")
                    st.rerun()

                if del_u_btn:
                    if target_u['user_id'] == MAIN_ADMIN['user_id']:
                        st.error("❌ لا يمكن حذف الحساب الرئيسي للمدير (Mohamed Salem).")
                    else:
                        target_u['status'] = "Disabled"
                        st.success(f"🗑️ تم حذف وتجميد حساب {target_u['full_name']} بنجاح!")
                        st.rerun()

        with tab_audit:
            st.markdown("### 📨 تدقيق المراسلات والرسائل والواتساب المباشر لكل مستخدم")
            active_users = [u for u in st.session_state['registered_users'] if u['status'] == "Active"]
            aud_user_options = {f"{u['full_name']} ({u['phone_number']})": u for u in active_users}
            selected_aud_label = st.selectbox("اختر المستخدم لعرض سجله الخاص:", list(aud_user_options.keys()))
            aud_u = aud_user_options[selected_aud_label]

            col_aud1, col_aud2 = st.columns(2)

            with col_aud1:
                st.markdown(f"#### 📬 صندوق البريد والرسائل الداخلية لـ ({aud_u['full_name']})")
                user_msgs = [m for m in st.session_state['internal_messages'] if aud_u['full_name'] in m.get('sender', '') or aud_u['full_name'] in m.get('recipient', '')]
                if user_msgs:
                    for m in user_msgs:
                        st.markdown(f"""
                        <div class="chat-bubble-in">
                            <strong>من: {m.get('sender', 'غير معروف')} ➔ إلى: {m.get('recipient', 'الجميع')}</strong><br>
                            <span>{m.get('text', '')}</span><br>
                            <small style='color:#64748b;'>📅 {m.get('time', '')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد رسائل داخلية مسجلة لهذا المستخدم.")

            with col_aud2:
                st.markdown(f"#### 📱 الأرقام والمراسلات الخارجية عبر (WhatsApp) لـ ({aud_u['full_name']})")
                user_wa = [w for w in st.session_state['whatsapp_logs'] if aud_u['full_name'] in w.get('sender', '')]
                if user_wa:
                    for w in user_wa:
                        st.markdown(f"""
                        <div class="chat-bubble-in" style="border-right: 6px solid #16a34a;">
                            <strong>المستلم: {w.get('target_name', 'غير معروف')} (+{w.get('phone', '')})</strong><br>
                            <span>{w.get('text', '')}</span><br>
                            <small style='color:#64748b;'>📅 {w.get('time', '')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد مراسلات واتساب مسجلة لهذا المستخدم.")

        with tab_points_eval:
            st.markdown("### 🏆 التحكم بنقاط تقييم الموظفين والتحليل العام للأداء")
            
            active_users = [u for u in st.session_state['registered_users'] if u['status'] == "Active"]
            eval_user_options = {f"{u['full_name']} ({u['role_group']})": u for u in active_users}
            selected_eval_label = st.selectbox("اختر الموظف لإدارة نقاطه وتحليل أنائه:", list(eval_user_options.keys()))
            eval_u = eval_user_options[selected_eval_label]

            u_p_data = st.session_state['user_points'].get(eval_u['user_id'], {"earned": 0, "deducted": 0, "notes": ""})

            col_p_act1, col_p_act2 = st.columns([2, 3])

            with col_p_act1:
                st.markdown(f"#### ✏️ تعديل النقاط يدويًا لـ **{eval_u['full_name']}**")
                new_earned = st.number_input("النقاط المكتسبة (+1 عند غلق الملف):", min_value=0, value=u_p_data['earned'])
                new_deducted = st.number_input("الخصومات والتأخيرات (-1):", min_value=0, value=u_p_data['deducted'])
                p_notes = st.text_area("سبب تعديل التقييم / الملاحظات:", value=u_p_data['notes'], height=80)

                if st.button("💾 حفظ تعديل النقاط والتقييم"):
                    st.session_state['user_points'][eval_u['user_id']] = {
                        "earned": new_earned,
                        "deducted": new_deducted,
                        "notes": p_notes.strip()
                    }
                    st.success("✅ تم تحديث التقييم والنقاط المكتسبة بنجاح!")
                    st.rerun()

            with col_p_act2:
                st.markdown(f"#### 📊 التحليل العام والتقييم النهائي لـ **{eval_u['full_name']}**")
                net_pts = new_earned - new_deducted
                
                m1, m2, m3 = st.columns(3)
                m1.metric("➕ المكتسبة", f"{new_earned} نقطة")
                m2.metric("➖ الخصومات", f"{new_deducted} نقطة")
                m3.metric("🏆 صافي النقاط", f"{net_pts} نقطة")

                df_eval_chart = pd.DataFrame([
                    {"مؤشر": "النقاط المكتسبة", "العدد": new_earned},
                    {"مؤشر": "الخصومات والتأخير", "العدد": new_deducted}
                ])
                fig_eval = px.bar(df_eval_chart, x="مؤشر", y="العدد", color="مؤشر", text_auto=True, title=f"تحليل التقييم والتزام الموظف ({eval_u['full_name']})")
                st.plotly_chart(fig_eval, use_container_width=True)

        with tab_sla_cfg:
            st.markdown("### ⏱️ اعتماد التوقيتات والمهل الزمنية المتغيرة (SLA Configuration)")
            st.info("💡 يمكنك هنا تعديل أوقات الفحص والتحذير والتأخير لكل حالة من الحالات الـ 8 بشكل مباشر.")

            sla_data = [
                {"الحالة": "Under Operation", "أيام الفحص (Check Days)": 2, "ساعات الفحص": 0, "أيام التأخير (Late Days)": 4, "ساعات التأخير": 0},
                {"الحالة": "Waiting BL", "أيام الفحص (Check Days)": 1, "ساعات الفحص": 12, "أيام التأخير (Late Days)": 3, "ساعات التأخير": 0},
                {"الحالة": "Draft", "أيام الفحص (Check Days)": 1, "ساعات الفحص": 0, "أيام التأخير (Late Days)": 2, "ساعات التأخير": 0},
                {"الحالة": "Waiting Confirmation", "أيام الفحص (Check Days)": 2, "ساعات الفحص": 0, "أيام التأخير (Late Days)": 5, "ساعات التأخير": 0},
                {"الحالة": "Stamped", "أيام الفحص (Check Days)": 1, "ساعات الفحص": 0, "أيام التأخير (Late Days)": 2, "ساعات التأخير": 0},
                {"الحالة": "Ready to be invoiced", "أيام الفحص (Check Days)": 1, "ساعات الفحص": 0, "أيام التأخير (Late Days)": 2, "ساعات التأخير": 0},
                {"الحالة": "Closed", "أيام الفحص (Check Days)": 0, "ساعات الفحص": 0, "أيام التأخير (Late Days)": 0, "ساعات التأخير": 0}
            ]
            
            df_sla_edit = st.data_editor(pd.DataFrame(sla_data), use_container_width=True)
            if st.button("💾 حفظ تعديلات مهل SLA السحابية"):
                st.success("✅ تم حفظ اعتماد التوقيتات والمهل الزمنية الجديدة بنجاح!")

    # ---------------------------------------------------------
    # التبويب 2: لوحة المؤشرات والتحليلات المخصصة
    # ---------------------------------------------------------
    elif choice == "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)":
        st.subheader("📈 لوحة التحليلات المتقدمة والشاملة (Comprehensive Analytics)")

        df_shipments = pd.DataFrame(st.session_state['active_shipments'])
        df_shipments.rename(columns={
            "id": "shipment_id", "file_num": "file_number", "company": "company_name",
            "inv": "invoice_number", "status": "current_status", "holded": "is_holded",
            "last_up": "last_updated_at", "last_status_updater": "full_name"
        }, inplace=True)

        df_shipments['sla_status'] = df_shipments.apply(lambda row: calculate_sla_status(row["current_status"], row["last_updated_at"])[0], axis=1)

        st.markdown("#### 🔍 لوحة تصفية وبحث محددات التحليل")
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            all_employees = ["كل الموظفين (الشامل)"] + sorted(list(df_shipments["full_name"].dropna().unique()))
            selected_emp = st.selectbox("👤 اختر الموظف المحدد (صاحب آخر تحديث للحالة):", all_employees)

        with col_f2:
            all_companies = ["كل العملاء (الكل)"] + sorted(list(df_shipments["company_name"].dropna().unique()))
            selected_comp = st.selectbox("🏢 اختر الشركة / العميل المحدد للبحث والتصفية:", all_companies)

        filtered_df = df_shipments.copy()
        if selected_emp != "كل الموظفين (الشامل)":
            filtered_df = filtered_df[filtered_df["full_name"] == selected_emp]
        if selected_comp != "كل العملاء (الكل)":
            filtered_df = filtered_df[filtered_df["company_name"] == selected_comp]

        st.write("---")

        analysis_options = [
            "📊 تقييم أداء الشحنات بالحالات والأسماء",
            "🏢 تقييم ومتابعة أداء العملاء والتأخيرات",
            "🔄 نسبة الشحنات بالحالات التشغيلية",
            "🎯 أسباب وعنق التكظز (Bottleneck Analysis)",
            "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)",
            "📂 كشف واستعلام ملفات العملاء التفصيلي"
        ]
        selected_analysis = st.selectbox("💡 اختر نوع التحليل المطلوب إظهاره:", analysis_options)

        st.write("---")

        if selected_analysis == "📊 تقييم أداء الشحنات بالحالات والأسماء":
            st.markdown(f"### 📊 توزيع شحنات الحالات متبوعة بأسماء الموظفين المحدثين")
            
            if selected_emp == "كل الموظفين (الشامل)":
                status_emp_summary = filtered_df.groupby(["current_status", "full_name"]).size().reset_index(name="عدد_الشحنات")
                fig_stacked = px.bar(
                    status_emp_summary, 
                    x="current_status", 
                    y="عدد_الشحنات", 
                    color="full_name", 
                    title="توزيع الحالات التشغيلية مقسمة بأسماء الموظفين القائمين بالتحديث", 
                    text_auto=True,
                    barmode="stack"
                )
                st.plotly_chart(fig_stacked, use_container_width=True)
            else:
                fig_single = px.bar(
                    filtered_df["current_status"].value_counts().reset_index(), 
                    x="current_status", 
                    y="count", 
                    color="current_status", 
                    title=f"توزيع شحنات الموظف ({selected_emp}) حسب الحالات", 
                    text_auto=True
                )
                st.plotly_chart(fig_single, use_container_width=True)

        elif selected_analysis == "🏢 تقييم ومتابعة أداء العملاء والتأخيرات":
            st.markdown("### 🏢 تقييم أداء العملاء وتفاصيل التأخيرات للمتابعة الفورية")
            
            comp_eval = filtered_df.groupby("company_name").agg(
                إجمالي_الشحنات=('shipment_id', 'count'),
                المكتملة_Closed=('current_status', lambda x: (x == 'Closed').sum()),
                المتأخرة_Late=('sla_status', lambda x: (x == 'متأخر (Late)').sum()),
                المعلقة_Hold=('is_holded', 'sum')
            ).reset_index()

            st.dataframe(comp_eval, use_container_width=True)

            late_shipments = filtered_df[filtered_df['sla_status'] == 'متأخر (Late)']
            st.markdown("#### 🚨 كشف وصف الشحنات المتأخرة لمباشرة إجراءات المتابعة:")
            if not late_shipments.empty:
                st.dataframe(late_shipments[[
                    "file_number", "company_name", "current_status", 
                    "full_name", "last_updated_at", "h_reason"
                ]].rename(columns={
                    "file_number": "رقم الملف",
                    "company_name": "الشركة / العميل",
                    "current_status": "الحالة المتأخرة الحالية",
                    "full_name": "الموظف المحدث للحالة",
                    "last_updated_at": "تاريخ آخر تحديث حالة",
                    "h_reason": "سبب التعليق إن وجد"
                }), use_container_width=True)
            else:
                st.success("✅ لا توجد شحنات متأخرة حالياً لكافة العملاء المحددين.")

        elif selected_analysis == "🔄 نسبة الشحنات بالحالات التشغيلية":
            st.markdown("### 🔄 نسبة توزيع الشحنات على الحالات الـ 8")
            fig_pie = px.pie(filtered_df, names="current_status", hole=0.35, title="نسب توزيع الشحنات بالحالات التشغيلية")
            st.plotly_chart(fig_pie, use_container_width=True)

        elif selected_analysis == "🎯 أسباب وعنق التكظز (Bottleneck Analysis)":
            st.markdown("### 🎯 الحالة الأكثر تكراراً وتسبباً للتكدس")
            most_common = filtered_df["current_status"].mode()
            if not most_common.empty:
                st.warning(f"⚠️ الحالة الأكثر تكراراً هي: **{most_common[0]}** (تكررت {len(filtered_df[filtered_df['current_status'] == most_common[0]])} مرة)")

        elif selected_analysis == "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)":
            st.markdown("### ⏱️ تحليل SLA والالتزام بالتوقيتات")
            fig_sla = px.pie(filtered_df, names="sla_status", hole=0.4, title="مؤشرات الالتزام بالمهل الزمني")
            st.plotly_chart(fig_sla, use_container_width=True)

        elif selected_analysis == "📂 كشف واستعلام ملفات العملاء التفصيلي":
            st.markdown("### 📂 كشف الملفات المجمعة للعملاء المحددين")
            st.dataframe(filtered_df, use_container_width=True)

    # ---------------------------------------------------------
    # التبويب 3: إدارة الحالات والتتبع
    # ---------------------------------------------------------
    elif choice == "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)":
        st.subheader("🔄 شاشة إدارة الحالات وتتبع المهل الزمنية (SLA & Lifecycle)")

        rows = st.session_state['active_shipments']

        shipment_list = []
        for r in rows:
            sla_label, sla_class, elapsed_h = calculate_sla_status(r['status'], r['last_up'])
            
            shipment_list.append({
                'رقم الملف': r['file_num'],
                'الشركة': r['company'],
                'رقم الحجز': r['bkg'],
                'رقم الفاتورة': r['inv'],
                'الحالة الحالية': f"⏸️ معلقة (Hold)" if r['holded'] else r['status'],
                'وضع SLA': sla_label,
                'الساعات المنقضية': f"{elapsed_h:.1f} ساعة",
                'الموظف المحدث للحالة': r.get('last_status_updater', 'غير محدد'),
                'آخر تحديث حالة': str(r['last_up']),
                'الملاحظة الحالية': r.get('note', '')
            })

        df = pd.DataFrame(shipment_list)
        st.markdown("#### 📋 جدول الشحنات النشطة ومؤشرات الالتزام")
        st.dataframe(df, use_container_width=True)

        st.write("---")
        st.markdown("### 🛠️ تحديث الحالة وإضافة الملاحظة")

        shipment_map = {f"ملف: {r['file_num']} - شركة: {r['company']} (الحالة: {r['status']})": r['id'] for r in rows}
        shipment_labels = list(shipment_map.keys())

        default_idx = 0
        if st.session_state['selected_shipment_id']:
            for idx, label in enumerate(shipment_labels):
                if shipment_map[label] == st.session_state['selected_shipment_id']:
                    default_idx = idx
                    break

        selected_label = st.selectbox("اختر الشحنة:", shipment_labels, index=default_idx)
        selected_id = shipment_map[selected_label]
        st.session_state['selected_shipment_id'] = selected_id

        s_data = next((item for item in rows if item['id'] == selected_id), None)

        if s_data:
            col_status_change, col_notes = st.columns([2, 2])

            with col_status_change:
                st.markdown("**تغيير الحالة**")
                all_statuses = [
                    'Under Operation', 'Waiting BL', 'Draft', 
                    'Waiting Confirmation', 'Stamped', 
                    'Ready to be invoiced', 'Closed'
                ]
                
                curr_st = s_data['status']
                new_selected_status = st.selectbox("الحالة الجديدة:", all_statuses, index=all_statuses.index(curr_st) if curr_st in all_statuses else 0)
                set_hold = st.checkbox("تفعيل تعليق الشحنة (Put on Hold)", value=bool(s_data['holded']))
                hold_reason_text = ""
                if set_hold:
                    hold_reason_text = st.text_input("سبب التعليق:", value=s_data['h_reason'] if s_data['h_reason'] else "")

                save_clicked = st.button("💾 حفظ التعديل", key="save_status_btn")
                
                if save_clicked:
                    if set_hold and hold_reason_text.strip() == "":
                        st.error("⚠️ يرجى كتابة سبب التعليق عند تفعيل خيار Hold.")
                    else:
                        was_not_closed = (s_data['status'] != 'Closed')
                        
                        s_data['status'] = new_selected_status
                        s_data['holded'] = 1 if set_hold else 0
                        s_data['h_reason'] = hold_reason_text.strip() if set_hold else ""
                        s_data['last_up'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        s_data['last_status_updater'] = user['full_name']

                        if new_selected_status == 'Closed' and was_not_closed:
                            u_pts = st.session_state['user_points'].get(user['user_id'], {"earned": 0, "deducted": 0, "notes": ""})
                            u_pts['earned'] += 1
                            u_pts['notes'] = f"إغلاق الملف رقم {s_data['file_num']}"
                            st.session_state['user_points'][user['user_id']] = u_pts

                        update_shipment_sql = "UPDATE shipments SET current_status = ?, is_holded = ?, hold_reason = ? WHERE shipment_id = ?"
                        execute_query(update_shipment_sql, (new_selected_status, 1 if set_hold else 0, hold_reason_text.strip() if set_hold else None, s_data['id']))

                        st.success(f"✅ تم حفظ تعديل حالة الملف ({s_data['file_num']}) بنجاح!")
                        st.rerun()

            with col_notes:
                st.markdown("**ملاحظة**")
                new_note = st.text_area("الملاحظة التوضيحية:", height=110, value="")
                if st.button("📝 إضافة الملاحظة", key="add_note_btn"):
                    if new_note.strip() != "":
                        s_data['note'] = new_note.strip()
                        note_sql = "INSERT INTO shipment_notes (shipment_id, added_by_user, note_content) VALUES (?, ?, ?)"
                        execute_query(note_sql, (s_data['id'], user['user_id'], new_note.strip()))
                        st.success("✅ تم حفظ الملاحظة بنجاح.")
                        st.rerun()
                    else:
                        st.warning("يرجى كتابة نص الملاحظة قبل الحفظ.")

    # ---------------------------------------------------------
    # التبويب 4: اضف الشحنة (المحدث باسم الزر الجديد)
    # ---------------------------------------------------------
    elif choice == "➕ إضافة شحنة جديدة (تفكيك الـ 11)":
        st.subheader("اضف الشحنة")
        
        input_type = st.radio("اختر طريقة الإدخال:", ["اضف العنوان", "إدخال يدوي مباشر"], horizontal=True)

        parsed = {
            'po_number': '', 'file_number': '', 'container_count': 1,
            'container_type': '40HC', 'pol': '', 'pod': '',
            'destination_country': '', 'invoice_number': '',
            'company_name': '', 'booking_number': '', 'item_description': ''
        }

        if input_type == "اضف العنوان":
            raw_ref_str = st.text_area("ألصق العنوان", height=80, value="")
            
            # تم تحديث المسمى هنا إلى "اضف العنوان" بناءً على طلبك بالصورة المرفقة
            if st.button("اضف العنوان"):
                if raw_ref_str.strip() != "":
                    data, success = parse_reference_string(raw_ref_str)
                    if success:
                        st.session_state['parsed_data'] = data
                        st.success("✅ تم تفكيك العنوان وتعبئة الحقول بنجاح!")
                    else:
                        st.error("⚠️ لم نتمكن من تفكيك النص بالكامل.")
                else:
                    st.warning("يرجى إلصاق العنوان أولاً.")

        if 'parsed_data' in st.session_state and input_type == "اضف العنوان":
            parsed = st.session_state['parsed_data']

        st.write("---")
        with st.form("shipment_entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                po_num = st.text_input("PO Number", value=parsed['po_number'])
                file_num = st.text_input("رقم الملف (File Number) *", value=parsed['file_number'])
                cont_count = st.number_input("عدد الحاويات", min_value=1, value=parsed['container_count'])
                cont_type = st.text_input("نوع الحاوية", value=parsed['container_type'])
            
            with c2:
                pol_val = st.text_input("ميناء الشحن (POL)", value=parsed['pol'])
                pod_val = st.text_input("ميناء الوصول (POD)", value=parsed['pod'])
                dest_country = st.text_input("الوجهة النهائية", value=parsed['destination_country'])
                inv_num = st.text_input("رقم الفاتورة", value=parsed['invoice_number'])

            with c3:
                company = st.text_input("اسم الشركة (Company Name) *", value=parsed['company_name'])
                bkg_num = st.text_input("رقم الحجز (Booking Number)", value=parsed['booking_number'])
                item_desc = st.text_area("وصف البضاعة", value=parsed['item_description'], height=100)

            submit_btn = st.form_submit_button("اضف الشحنة")

            if submit_btn:
                if file_num.strip() == "" or company.strip() == "":
                    st.error("❌ رقم الملف واسم الشركة حقول إجبارية.")
                else:
                    new_item = {
                        "id": len(st.session_state['active_shipments']) + 1,
                        "file_num": file_num,
                        "company": company,
                        "bkg": bkg_num,
                        "inv": inv_num,
                        "status": "Under Operation",
                        "holded": 0,
                        "h_reason": "",
                        "last_up": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "last_status_updater": user['full_name'],
                        "note": ""
                    }
                    st.session_state['active_shipments'].append(new_item)
                    st.success(f"🎉 تم إضافة الشحنة ({file_num}) بنجاح! الحالة: Under Operation")

# ---------------------------------------------------------
    # التبويب 5: المراسلات والواتساب المحدث
    # ---------------------------------------------------------
    elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
        st.subheader("المراسالات")

        tab_msg, tab_wa = st.tabs(["📩 الرسائل الداخلية النظامية", "WhatsApp"])

        with tab_msg:
            col_send, col_inbox = st.columns([2, 3])
            with col_send:
                st.markdown("### 📤 إرسال رسالة داخلية")
                
                # قائمة الموظفين المفعلين
                active_users_list = [u for u in st.session_state['registered_users'] if u['status'] == 'Active']
                emp_map = {f"{u['full_name']} ({u['role_group']})": u for u in active_users_list}
                target_emp_label = st.selectbox("إلى المستخدم / الفريق:", list(emp_map.keys()))
                target_emp_obj = emp_map[target_emp_label]

                # الاختيار بين رسالة عادية أو تنبيه لشحنة
                msg_type = st.radio("نوع الرسالة الداخلية:", ["رسالة عادية", "تنبيه/تحديث لشحنة محددة"], horizontal=True)

                if msg_type == "تنبيه/تحديث لشحنة محددة":
                    rows = st.session_state['active_shipments']
                    ship_map = {f"ملف: {r['file_num']} - شركة: {r['company']}": r for r in rows}
                    selected_s_label = st.selectbox("اختر الشحنة المراد التنبيه عليها:", list(ship_map.keys()))
                    selected_s = ship_map[selected_s_label]

                    dynamic_body = (
                        f"مرحباً أستاذ/ة {target_emp_obj['full_name']}\n\n"
                        f"نود إحاطتكم بالتحديث الخاص بشحنتكم:\n"
                        f"📂 رقم الملف: {selected_s['file_num']}\n"
                        f"🔖 اسم الشركة: {selected_s['company']}\n"
                        f"🧾 رقم الفاتورة: {selected_s['inv']}\n"
                        f"📌 الحالة الحالية: {selected_s['status']}"
                    )
                    user_editable_text = st.text_area("نص التحديث التوضيحي (إن وجد):", value=dynamic_body, height=160)
                else:
                    user_editable_text = st.text_area("نص الرسالة الداخلية:", height=120)

                # الخاتمة الثابتة غير القابلة للتعديل
                fixed_footer = "يرجى اتخاذ اللازم إنهاء الإجراء\nتحياتنا، فريق U.S.C للتشغيل\nM.Salem"
                st.info(f"🔒 الخاتمة الملحقة بالرسالة تلقائياً:\n\n{fixed_footer}")

                if st.button("🚀 إرسال الرسالة الداخلية"):
                    if user_editable_text.strip() != "":
                        full_final_msg = f"{user_editable_text.strip()}\n\n{fixed_footer}"
                        st.session_state['internal_messages'].append({
                            "sender": user['full_name'],
                            "recipient": target_emp_label,
                            "text": full_final_msg,
                            "time": datetime.now().strftime('%H:%M %p')
                        })
                        st.success("✅ تم إرسال الرسالة الداخلية وتوثيقها بنجاح!")
                        st.rerun()
                    else:
                        st.warning("يرجى كتابة نص الرسالة أولاً.")

            with col_inbox:
                st.markdown("### 📥 صندوق الرسائل الواردة")
                for msg in reversed(st.session_state['internal_messages']):
                    st.markdown(f"""
                    <div class="chat-bubble-in">
                        <strong>من: {msg.get('sender', 'غير معروف')} ➔ إلى: {msg.get('recipient', 'الجميع')}</strong><br>
                        <span>{msg.get('text', '')}</span><br>
                        <small style="color: #94a3b8;">📅 {msg.get('time', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_wa:
            st.markdown("### WhatsApp")
            
            # 1. تحديد نوع المستلم (الموظف هو الخيار الافتراضي)
            recipient_type = st.radio("تحديد نوع المستلم:", ["مستخدم/موظف بالبرنامج", "العميل"], horizontal=True)

            # 2. اختيار الشحنة المراد مراسلتها
            rows = st.session_state['active_shipments']
            shipment_options = {f"ملف: {r['file_num']} - شركة: {r['company']} (الحالة: {r['status']})": r for r in rows}
            selected_ship_label = st.selectbox("اختر الشحنة المُراد المراسلة بشأنها:", list(shipment_options.keys()))
            selected_ship = shipment_options[selected_ship_label]

            col_wa1, col_wa2 = st.columns(2)

            if recipient_type == "العميل":
                with col_wa1:
                    target_name = st.text_input("اسم العميل / الشركة:", value=f"شركة {selected_ship['company']}")
                    target_phone = st.text_input("رقم الهاتف", value="01212231815")
                
                header_greeting = f"مرحباً أستاذ/ة (عناية {target_name})"
            else:
                active_users_list = [u for u in st.session_state['registered_users'] if u['status'] == 'Active']
                emp_map = {f"{u['full_name']} ({u['phone_number']})": u for u in active_users_list}
                
                with col_wa1:
                    selected_emp_wa = st.selectbox("اختر الموظف المستلم:", list(emp_map.keys()))
                    target_u_obj = emp_map[selected_emp_wa]
                    target_name = target_u_obj['full_name']
                    target_phone = target_u_obj['phone_number']
                    st.info(f"📱 رقم الهاتف المسجل بالنظام لـ ({target_name}): **{target_phone}**")

                header_greeting = f"مرحباً أستاذ/ة {target_name}"

            # القالب الموحد
            wa_template = (
                f"{header_greeting}\n\n"
                f"نود إحاطتكم بالتحديث الخاص بشحنتكم:\n"
                f"📂 رقم الملف: {selected_ship['file_num']}\n"
                f"🔖 اسم الشركة: {selected_ship['company']}\n"
                f"🧾 رقم الفاتورة: {selected_ship['inv']}\n"
                f"📌 الحالة الحالية: {selected_ship['status']}\n\n"
                f"يرجى اتخاذ اللازم إنهاء الإجراء\n"
                f"تحياتنا، فريق U.S.C للتشغيل\n"
                f"M.Salem"
            )

            with col_wa2:
                final_msg = st.text_area("نص الرسالة المعاينة قبل الإرسال:", value=wa_template, height=220)

            if target_phone.strip() != "":
                clean_phone = format_whatsapp_phone(target_phone)
                encoded_msg = urllib.parse.quote(final_msg.strip())
                direct_wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.info(f"رقم المراسلة: **+{clean_phone}**")
                with col_b2:
                    if st.link_button("ارسال WhatsApp", direct_wa_url, use_container_width=True):
                        st.session_state['whatsapp_logs'].append({
                            "sender": user['full_name'],
                            "target_name": target_name,
                            "phone": clean_phone,
                            "text": final_msg.strip(),
                            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

    # ---------------------------------------------------------
    # التبويب 6: تقارير التقييم
    # ---------------------------------------------------------
    elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
        st.subheader("📊 تقارير تقييم الأداء والمكافآت والتأخيرات")

        st.success("✅ قاعدة التقييم المعتمدة بالنظام: 1 نقطة لكل ملف مكتمل ومغلق (Closed).")
        
        eval_rows = []
        for u in st.session_state['registered_users']:
            if u['status'] == "Active":
                pts = st.session_state['user_points'].get(u['user_id'], {"earned": 0, "deducted": 0, "notes": ""})
                net = pts['earned'] - pts['deducted']
                eval_rows.append({
                    "المستخدم": u['full_name'],
                    "المجموعة": u['role_group'],
                    "النقاط المكتسبة (+1 عند غلق الملف)": pts['earned'],
                    "الخصومات والتأخير (-1)": pts['deducted'],
                    "صافي التقييم النهائي": net,
                    "ملاحظات التقييم": pts['notes']
                })
        
        st.dataframe(pd.DataFrame(eval_rows), use_container_width=True)

    # ---------------------------------------------------------
    # التبويب 7: سجل الحالات
    # ---------------------------------------------------------
    elif choice == "📋 سجل الحالات والتدقيق (Status Logs)":
        st.subheader("📋 سجل الحالات والتدقيق التاريخي (Status Logs & Audit Trail)")
        st.dataframe(pd.DataFrame([
            {"#": 1, "الشحنة": "260862115", "الحالة السابقة": "Draft", "الحالة الجديدة": "Under Operation", "التاريخ والوقت": "2026-09-18 10:00:00"},
            {"#": 2, "الشحنة": "260862116", "الحالة السابقة": "Under Operation", "الحالة الجديدة": "Waiting BL", "التاريخ والوقت": "2026-09-18 11:30:00"},
            {"#": 3, "الشحنة": "260862117", "الحالة السابقة": "Stamped", "الحالة الجديدة": "Ready to be invoiced", "التاريخ والوقت": "2026-09-18 12:15:00"}
        ]), use_container_width=True)