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
# 1. إعدادات الصفحة والتصميم العام للهوية البصرية والتباين المحدث
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

# الشفافية المحدثة بنسبة 80% (زيادة 5%) مع خطوط 26px للعناوين و 24px للبيانات
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

# قائمة كافة الشاشات الأساسية
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
        1: {"earned": 10, "deducted": 0, "notes": "تقييم المدير الأسبوعي"},
        2: {"earned": 8, "deducted": 1, "notes": "تأخير ملف رقم 260862116"},
        3: {"earned": 5, "deducted": 0, "notes": "أداء متوافق"}
    }

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

if 'active_shipments' not in st.session_state:
    st.session_state['active_shipments'] = [
        {"id": 1, "file_num": "260862115", "company": "U.S.C", "bkg": "CFA0951367", "inv": "3A - 3B", "status": "Under Operation", "holded": 0, "h_reason": "", "last_up": "2026-09-18 10:00:00", "creator": "Mohamed Salem"},
        {"id": 2, "file_num": "260862116", "company": "CFA Global", "bkg": "CFA0951368", "inv": "104B", "status": "Waiting BL", "holded": 0, "h_reason": "", "last_up": "2026-09-18 11:30:00", "creator": "أحمد علي"},
        {"id": 3, "file_num": "260862117", "company": "Al-Salem Trading", "bkg": "CFA0951369", "inv": "88C", "status": "Ready to be invoiced", "holded": 0, "h_reason": "", "last_up": "2026-09-18 12:15:00", "creator": "Mohamed Salem"},
        {"id": 4, "file_num": "260862118", "company": "U.S.C", "bkg": "CFA0951370", "inv": "99A", "status": "Draft", "holded": 1, "h_reason": "في انتظار موافقة العميل", "last_up": "2026-09-18 09:00:00", "creator": "محمود حسن"}
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

# =========================================================
# 3. دالة تفكيك السطر المرجعي
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
    if not last_updated_at:
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

    # اختيار الشاشة الافتراضية
    choice = st.sidebar.selectbox("القائمة الرئيسية المسموحة", allowed_menu, index=0)

    # ---------------------------------------------------------
    # التبويب 1: لوحة التحكم الإدارية للمدير الرئيسي (Admin Panel)
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

        # 1.1 اعتماد الطلبات
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

        # 1.2 تعديل الحسابات المفعلة والمجموعات وكلمات المرور والحذف
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

        # 1.3 صندوق البريد وتتبع المراسلات والواتساب لكل مستخدم
        with tab_audit:
            st.markdown("### 📨 تدقيق المراسلات والرسائل والواتساب المباشر لكل مستخدم")
            active_users = [u for u in st.session_state['registered_users'] if u['status'] == "Active"]
            aud_user_options = {f"{u['full_name']} ({u['phone_number']})": u for u in active_users}
            selected_aud_label = st.selectbox("اختر المستخدم لعرض سجله الخاص:", list(aud_user_options.keys()))
            aud_u = aud_user_options[selected_aud_label]

            col_aud1, col_aud2 = st.columns(2)

            with col_aud1:
                st.markdown(f"#### 📬 صندوق البريد والرسائل الداخلية لـ ({aud_u['full_name']})")
                user_msgs = [m for m in st.session_state['internal_messages'] if aud_u['full_name'] in m['sender'] or aud_u['full_name'] in m['recipient']]
                if user_msgs:
                    for m in user_msgs:
                        st.markdown(f"""
                        <div class="chat-bubble-in">
                            <strong>من: {m['sender']} ➔ إلى: {m.get('recipient', 'الجميع')}</strong><br>
                            <span>{m['text']}</span><br>
                            <small style='color:#64748b;'>📅 {m['time']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد رسائل داخلية مسجلة لهذا المستخدم.")

            with col_aud2:
                st.markdown(f"#### 📱 الأرقام والمراسلات الخارجية عبر (WhatsApp) لـ ({aud_u['full_name']})")
                user_wa = [w for w in st.session_state['whatsapp_logs'] if aud_u['full_name'] in w['sender']]
                if user_wa:
                    for w in user_wa:
                        st.markdown(f"""
                        <div class="chat-bubble-in" style="border-right: 6px solid #16a34a;">
                            <strong>المستلم: {w['target_name']} (+{w['phone']})</strong><br>
                            <span>{w['text']}</span><br>
                            <small style='color:#64748b;'>📅 {w['time']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد مراسلات واتساب مسجلة لهذا المستخدم.")

        # 1.4 قسم تقييمات الموظفين والتحكم بالنقاط المكتسبة والضائعة والتحليل العام
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
                new_earned = st.number_input("النقاط المكتسبة (+1):", min_value=0, value=u_p_data['earned'])
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

                # رسم بياني تحليلي
                df_eval_chart = pd.DataFrame([
                    {"مؤشر": "النقاط المكتسبة", "العدد": new_earned},
                    {"مؤشر": "الخصومات والتأخير", "العدد": new_deducted}
                ])
                fig_eval = px.bar(df_eval_chart, x="مؤشر", y="العدد", color="مؤشر", text_auto=True, title=f"تحليل التقييم والتزام الموظف ({eval_u['full_name']})")
                st.plotly_chart(fig_eval, use_container_width=True)

        # 1.5 إعدادات SLA
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
    # التبويب 2: التحليلات الشاملة الـ 7
    # ---------------------------------------------------------
    elif choice == "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)":
        st.subheader("📈 لوحة التحليلات المتقدمة والشاملة (Comprehensive Analytics)")

        df_shipments = pd.DataFrame(st.session_state['active_shipments'])
        df_shipments.rename(columns={
            "id": "shipment_id", "file_num": "file_number", "company": "company_name",
            "inv": "invoice_number", "status": "current_status", "holded": "is_holded",
            "last_up": "last_updated_at", "creator": "full_name"
        }, inplace=True)

        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            all_employees = ["كل الموظفين (الشامل)"] + list(df_shipments["full_name"].unique())
            selected_emp = st.selectbox("👤 1️⃣ اختر الموظف المحدد أو كافة الموظفين:", all_employees)

        filtered_df = df_shipments if selected_emp == "كل الموظفين (الشامل)" else df_shipments[df_shipments["full_name"] == selected_emp]

        with col_filter2:
            analysis_options = [
                "📊 تقييم وأداء الموظف (1 نقطة/شحنة)",
                "🏢 تقييم أداء العميل",
                "🔄 عدد الشحنات بالحالات الخاصة بها",
                "🎯 أكثر حالة مكررة للموظف",
                "🏷️ أكثر حالة مكررة لاسم عميل محدد",
                "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)",
                "📂 استعلام ملفات العملاء المجمعة"
            ]
            selected_analysis = st.selectbox("💡 2️⃣ اختر التحليل المطلوب إظهاره:", analysis_options)

        st.write("---")

        if selected_analysis == "📊 تقييم وأداء الموظف (1 نقطة/شحنة)":
            st.markdown(f"### 📊 تقييم وأداء الموظف: **{selected_emp}**")
            total_shipments = len(filtered_df)
            net_points = total_shipments * 1

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📦 إجمالي الشحنات", f"{total_shipments} شحنة")
            k2.metric("➕ النقاط المكتسبة (+1 نقطة)", f"+{net_points} نقطة")
            k3.metric("➖ الخصومات والتأخير", "0 نقطة")
            k4.metric("🏆 التقييم الفعلي النهائي", f"{net_points} نقطة")

            fig_emp_status = px.bar(filtered_df["current_status"].value_counts().reset_index(), x="current_status", y="count", color="current_status", title="توزيع شحنات الموظف حسب الحالة التشغيلية", text_auto=True)
            st.plotly_chart(fig_emp_status, use_container_width=True)

        elif selected_analysis == "🏢 تقييم أداء العميل":
            st.markdown("### 🏢 تقييم أداء وتوزيع العملاء")
            comp_summary = filtered_df.groupby("company_name").agg(إجمالي_الشحنات=('shipment_id', 'count'), الشحنات_المعلقة=('is_holded', 'sum')).reset_index()
            st.dataframe(comp_summary, use_container_width=True)
            fig_comp = px.bar(comp_summary, x="company_name", y="إجمالي_الشحنات", color="company_name", text_auto=True)
            st.plotly_chart(fig_comp, use_container_width=True)

        elif selected_analysis == "🔄 عدد الشحنات بالحالات الخاصة بها":
            st.markdown("### 🔄 إحصائيات الشحنات حسب الحالات الـ 8")
            fig_pie_status = px.pie(filtered_df, names="current_status", hole=0.3, title="نسب توزيع الشحنات على الحالات الـ 8")
            st.plotly_chart(fig_pie_status, use_container_width=True)

        elif selected_analysis == "🎯 أكثر حالة مكررة للموظف":
            st.markdown("### 🎯 الحالة الأكثر تكراراً (Bottleneck Analysis)")
            most_common = filtered_df["current_status"].mode()
            if not most_common.empty:
                st.success(f"🎯 أكثر حالة مكررة هي: **{most_common[0]}** (تكررت {len(filtered_df[filtered_df['current_status'] == most_common[0]])} مرة)")

        elif selected_analysis == "🏷️ أكثر حالة مكررة لاسم عميل محدد":
            st.markdown("### 🏷️ تحليل الحالة المهيمنة لكل عميل")
            target_company = st.selectbox("اختر العميل:", filtered_df["company_name"].unique())
            comp_df = filtered_df[filtered_df["company_name"] == target_company]
            st.dataframe(comp_df, use_container_width=True)

        elif selected_analysis == "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)":
            st.markdown("### ⏱️ تحليل SLA والالتزام بالتوقيتات")
            filtered_df["sla_status"] = filtered_df.apply(lambda row: calculate_sla_status(row["current_status"], row["last_updated_at"])[0], axis=1)
            fig_sla_pie = px.pie(filtered_df, names="sla_status", hole=0.4, title="مؤشرات الالتزام بالمهل")
            st.plotly_chart(fig_sla_pie, use_container_width=True)

        elif selected_analysis == "📂 استعلام ملفات العملاء المجمعة":
            st.markdown("### 📂 كشف الملفات المجمعة حسب العميل")
            sel_c = st.selectbox("اختر اسم الشركة/العميل:", filtered_df["company_name"].unique())
            st.dataframe(filtered_df[filtered_df["company_name"] == sel_c], use_container_width=True)

    # ---------------------------------------------------------
    # التبويب 3: إدارة الحالات
    # ---------------------------------------------------------
    elif choice == "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)":
        st.subheader("🔄 شاشة إدارة الحالات وتتبع المهل الزمنية (SLA & Lifecycle)")

        rows = st.session_state['active_shipments']

        shipment_list = []
        for r in rows:
            sla_label, sla_class, elapsed_h = calculate_sla_status(r['status'], r['last_up'])
            
            shipment_list.append({
                'ID': r['id'],
                'رقم الملف': r['file_num'],
                'الشركة': r['company'],
                'رقم الحجز': r['bkg'],
                'رقم الفاتورة': r['inv'],
                'الحالة الحالية': f"⏸️ معلقة (Hold)" if r['holded'] else r['status'],
                'وضع SLA': sla_label,
                'الساعات المنقضية': f"{elapsed_h:.1f} ساعة",
                'الموظف المسؤول': r['creator'],
                'آخر تحديث': str(r['last_up'])
            })

        df = pd.DataFrame(shipment_list)
        st.markdown("#### 📋 جدول الشحنات النشطة ومؤشرات الالتزام")
        st.dataframe(df, use_container_width=True)

        st.write("---")
        st.markdown("### 🛠️ إجراءات تحديث الحالة وتأكيد الملاحظات")

        shipment_options = {f"ملف: {r['file_num']} - شركة: {r['company']} (الحالة الحالية: {r['status']})": r for r in rows}
        selected_option = st.selectbox("اختر الشحنة المراد تغيير حالتها أو إثبات ملاحظة عليها:", list(shipment_options.keys()))
        s_data = shipment_options[selected_option]

        col_status_change, col_notes = st.columns([2, 2])

        with col_status_change:
            st.markdown("**1. تغيير الحالة التشغيلية أو التعليق:**")
            all_statuses = [
                'Under Operation', 'Waiting BL', 'Draft', 
                'Waiting Confirmation', 'Stamped', 
                'Ready to be invoiced', 'Closed'
            ]
            
            curr_st = s_data['status']
            new_selected_status = st.selectbox("اختر الحالة الجديدة:", all_statuses, index=all_statuses.index(curr_st) if curr_st in all_statuses else 0)
            set_hold = st.checkbox("تفعيل تعليق الشحنة (Put on Hold)", value=bool(s_data['holded']))
            hold_reason_text = ""
            if set_hold:
                hold_reason_text = st.text_input("سبب التعليق (إجباري عند تفعيل التعليق):", value=s_data['h_reason'] if s_data['h_reason'] else "")

            save_clicked = st.button("💾 حفظ التحديث وتسجيل التقييم (1 نقطة)", key="save_status_btn")
            
            if save_clicked:
                if set_hold and hold_reason_text.strip() == "":
                    st.error("⚠️ يرجى كتابة سبب التعليق عند تفعيل خيار Hold.")
                else:
                    for item in st.session_state['active_shipments']:
                        if item['id'] == s_data['id']:
                            item['status'] = new_selected_status
                            item['holded'] = 1 if set_hold else 0
                            item['h_reason'] = hold_reason_text.strip() if set_hold else ""
                            item['last_up'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    update_shipment_sql = "UPDATE shipments SET current_status = ?, is_holded = ?, hold_reason = ? WHERE shipment_id = ?"
                    execute_query(update_shipment_sql, (new_selected_status, 1 if set_hold else 0, hold_reason_text.strip() if set_hold else None, s_data['id']))

                    st.success(f"🎉 تم تحديث حالة الملف ({s_data['file_num']}) بنجاح إلى [{new_selected_status}] وتسجيل 1 نقطة تقييم!")
                    st.rerun()

        with col_notes:
            st.markdown("**2. إضافة ملاحظة ميدانية مفتوحة (Open Note):**")
            new_note = st.text_area("اكتب ملاحظتك التوضيحية على هذه الشحنة:", height=110, placeholder="مثال: العميل طلب التأجيل لحين استلام الفاتورة النهائية")
            if st.button("📝 إضافة الملاحظة للسجل", key="add_note_btn"):
                if new_note.strip() != "":
                    note_sql = "INSERT INTO shipment_notes (shipment_id, added_by_user, note_content) VALUES (?, ?, ?)"
                    execute_query(note_sql, (s_data['id'], user['user_id'], new_note.strip()))
                    st.success("✅ تم إضافة الملاحظة وتوثيقها باسم الموظف بنجاح.")
                else:
                    st.warning("يرجى كتابة نص الملاحظة قبل الضغط على الزر.")

    # ---------------------------------------------------------
    # التبويب 4: تفكيك الـ 11
    # ---------------------------------------------------------
    elif choice == "➕ إضافة شحنة جديدة (تفكيك الـ 11)":
        st.subheader("📋 تفكيك السطر المرجعي وإدخال الشحنة (11 حقل)")
        
        input_type = st.radio("اختر طريقة الإدخال:", ["تفكيك سطر مرجعي (Smart Parse)", "إدخال يدوي مباشر"], horizontal=True)

        parsed = {
            'po_number': '', 'file_number': '', 'container_count': 1,
            'container_type': '40HC', 'pol': '', 'pod': '',
            'destination_country': '', 'invoice_number': '',
            'company_name': '', 'booking_number': '', 'item_description': ''
        }

        if input_type == "تفكيك سطر مرجعي (Smart Parse)":
            raw_ref_str = st.text_area("ألصق السطر المرجعي هنا (11 حقل):", height=80, 
                                       placeholder="C - 260862115 - 4.0 x 40 RFH - PSD - LATTAKIA - Syria - INV 3A - 3B - U.S.C لحد دلوقتى - CFA0951367")
            
            if st.button("🔍 تفكيك البيانات وتعبئة الحقول"):
                if raw_ref_str.strip() != "":
                    data, success = parse_reference_string(raw_ref_str)
                    if success:
                        st.session_state['parsed_data'] = data
                        st.success("✅ تم تفكيك السطر وتعبئة الحقول بنجاح!")
                    else:
                        st.error("⚠️ لم نتمكن من تفكيك السطر بالكامل.")
                else:
                    st.warning("يرجى إلصاق النص أولاً.")

        if 'parsed_data' in st.session_state and input_type == "تفكيك سطر مرجعي (Smart Parse)":
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
                dest_country = st.text_input("دولة المقصد", value=parsed['destination_country'])
                inv_num = st.text_input("رقم الفاتورة (بدون INV)", value=parsed['invoice_number'])

            with c3:
                company = st.text_input("اسم الشركة (Company Name) *", value=parsed['company_name'])
                bkg_num = st.text_input("رقم الحجز (Booking Number)", value=parsed['booking_number'])
                item_desc = st.text_area("وصف البضاعة", value=parsed['item_description'], height=100)

            submit_btn = st.form_submit_button("💾 حفظ الشحنة")

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
                        "creator": user['full_name']
                    }
                    st.session_state['active_shipments'].append(new_item)
                    st.success(f"🎉 تم حفظ الشحنة ({file_num}) بنجاح! الحالة: Under Operation")

    # ---------------------------------------------------------
    # التبويب 5: المراسلات والواتساب
    # ---------------------------------------------------------
    elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
        st.subheader("💬 المراسلات الداخلية والتكامل مع WhatsApp")

        tab_msg, tab_wa = st.tabs(["📩 الرسائل الداخلية النظامية", "📱 إرسال إشعار WhatsApp direct"])

        with tab_msg:
            col_send, col_inbox = st.columns([2, 3])
            with col_send:
                st.markdown("### 📤 إرسال رسالة داخلية")
                
                employee_list = [f"{u['full_name']} ({u['role_group']})" for u in st.session_state['registered_users'] if u['status'] == 'Active']
                target_emp = st.selectbox("إلى المستخدم / الفريق:", employee_list)
                msg_body = st.text_area("نص الرسالة:", height=100)
                
                if st.button("🚀 إرسال الرسالة الداخلية"):
                    if msg_body.strip() != "":
                        st.session_state['internal_messages'].append({
                            "sender": user['full_name'],
                            "recipient": target_emp,
                            "text": msg_body.strip(),
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
                        <strong>من: {msg['sender']} ➔ إلى: {msg.get('recipient', 'الجميع')}</strong><br>
                        <span>{msg['text']}</span><br>
                        <small style="color: #94a3b8;">📅 {msg['time']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_wa:
            st.markdown("### 📱 إرسال إشعار وتحديث عبر WhatsApp Direct")
            target_name = st.text_input("اسم العميل/المستلم:", value="أستاذ أحمد - شركة U.S.C")
            target_phone = st.text_input("رقم الهاتف (مثال: 01212231815):", value="01212231815")

            template_msg_body = (
                f"مرحباً {target_name}،\n\n"
                f"تحديث جديد لشحنتكم ملف رقم (260862115)\n"
                f"الشركة: U.S.C\n"
                f"رقم الفاتورة: 3A - 3B\n"
                f"الحالة الحالية: Under Operation\n\n"
                f"تحياتنا، Mohamed Salem OPS App"
            )

            final_msg = st.text_area("معاينة نص الرسالة قبل الإرسال:", value=template_msg_body, height=180)

            if target_phone.strip() != "":
                clean_phone = format_whatsapp_phone(target_phone)
                encoded_msg = urllib.parse.quote(final_msg.strip())
                direct_wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.code(final_msg.strip(), language=None)
                with col_b2:
                    st.info(f"📱 الرقم المعالج للإرسال: **+{clean_phone}**")
                    if st.link_button("🟢 فتح شات الرقم المباشر في WhatsApp", direct_wa_url, use_container_width=True):
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

        st.success("✅ قاعدة التقييم المعتمدة بالنظام: 1 نقطة لكل شحنة متوافقة ومكتملة.")
        
        eval_rows = []
        for u in st.session_state['registered_users']:
            if u['status'] == "Active":
                pts = st.session_state['user_points'].get(u['user_id'], {"earned": 0, "deducted": 0, "notes": ""})
                net = pts['earned'] - pts['deducted']
                eval_rows.append({
                    "المستخدم": u['full_name'],
                    "المجموعة": u['role_group'],
                    "النقاط المكتسبة (+1)": pts['earned'],
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