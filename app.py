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
    elif choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
        if user['role_group'] != "Admin":
            st.error("🚫 هذه الصفحة مخصصة لمدير النظام فقط.")
        else:
            st.subheader("⚙️ لوحة التحكم الإدارية (Admin Panel)")
            
            tab_u, tab_add = st.tabs(["👥 إدارة المستخدمين وصلاحيات الهيكل", "➕ إضافة مستخدم جديد"])

            with tab_u:
                st.markdown("### 📋 قائمة المستخدمين المفعلين بالنظام")
                users_data = []
                for idx, u_item in enumerate(st.session_state['registered_users'], start=1):
                    users_data.append({
                        "#": idx,
                        "اسم المستخدم": u_item['username'],
                        "الاسم بالكامل": u_item['full_name'],
                        "المجموعة الصلاحية": u_item['role_group'],
                        "رقم الهاتف": u_item.get('phone_number', 'غير مسجل'),
                        "حالة الحساب": "مفعل" if u_item['status'] == "Active" else "معطل"
                    })
                
                st.dataframe(pd.DataFrame(users_data), use_container_width=True)

            with tab_add:
                st.markdown("### ➕ إضافة حساب مستخدم جديد")
                with st.form("add_user_form_admin"):
                    new_u_username = st.text_input("اسم المستخدم (Username):")
                    new_u_fullname = st.text_input("الاسم الكامل:")
                    new_u_phone = st.text_input("رقم الهاتف (مثال: 01212231815):", value="01212231815")
                    new_u_role = st.selectbox("المجموعة الصلاحية:", ["Admin", "Management", "Operations", "Sales", "Customer Service"])
                    new_u_pass = st.text_input("كلمة المرور:", type="password")
                    
                    submit_user = st.form_submit_button("إضافة المستخدم")
                    if submit_user:
                        if new_u_username and new_u_fullname and new_u_pass:
                            new_id = max([u['user_id'] for u in st.session_state['registered_users']]) + 1
                            st.session_state['registered_users'].append({
                                "user_id": new_id,
                                "username": new_u_username.strip(),
                                "password": new_u_pass.strip(),
                                "full_name": new_u_fullname.strip(),
                                "role_group": new_u_role,
                                "phone_number": new_u_phone.strip(),
                                "status": "Active"
                            })
                            st.success(f"✅ تم إضافة المستخدم {new_u_fullname} بنجاح!")
                            st.rerun()
                        else:
                            st.warning("يرجى تعبئة كافة الحقول المطلوبة.")

    # ---------------------------------------------------------
    # التبويب 6: تقييم الأداء والبطاقة المعتمدة بالكامل (Performance & Bonus)
    # ---------------------------------------------------------
    elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
        st.subheader("تقييم الاداء")

        if 'initial_user_points' not in st.session_state:
            st.session_state['initial_user_points'] = {
                1: {"earned": 2, "deducted": 0, "notes": "إغلاق ملفات مكتملة"},
                2: {"earned": 1, "deducted": 1, "notes": "إغلاق ملف وتأخير سابقتين"},
                3: {"earned": 0, "deducted": 0, "notes": ""}
            }

        if 'user_photos' not in st.session_state:
            st.session_state['user_photos'] = {}

        st.success("✅ قاعدة التقييم المعتمدة بالنظام: 1 نقطة لكل ملف مكتمل ومغلق (Closed).")

        # --- لوحة التحكم لتشكيل وفلترة التقرير ---
        st.markdown("#### 🎛️ لوحة التحكم لتشكيل وفلترة تقارير الأداء")
        c_f1, c_f2 = st.columns(2)

        active_users_eval = [u for u in st.session_state['registered_users'] if u['status'] == "Active"]
        emp_names_list = ["الكل"] + [u['full_name'] for u in active_users_eval]

        with c_f1:
            filter_emp = st.selectbox("👤 تحديد الموظف:", emp_names_list)
        with c_f2:
            filter_rank = st.selectbox("🏆 ترتيب الأداء والتقييم:", ["الكل (افتراضي)", "الأعلى تقييماً (Top Performers)", "الأقل تقييماً (Lowest Performers)"])

        # استخراج وتجهيز البيانات
        raw_eval_list = []
        for u in active_users_eval:
            pts = st.session_state['user_points'].get(u['user_id'], {"earned": 0, "deducted": 0, "notes": ""})
            net = pts['earned'] - pts['deducted']
            
            emp_shipments = [s for s in st.session_state['active_shipments'] if s.get('last_status_updater') == u['full_name']]
            closed_ops = len([s for s in emp_shipments if s.get('status') == 'Closed'])
            total_ops = len(emp_shipments)
            emp_companies = list(set([s['company'] for s in emp_shipments if 'company' in s and s['company']]))
            
            if closed_ops > 0:
                ratio = (pts['earned'] / closed_ops) * 100.0
                if ratio > 100.0: ratio = 100.0
            elif pts['earned'] > 0:
                ratio = 100.0
            else:
                ratio = 0.0

            if ratio < 50.0 and pts['earned'] == 0:
                rating_category = "يحتاج الى الملاحظة"
            elif ratio == 50.0:
                rating_category = "طبيعي"
            elif 50.0 < ratio <= 75.0:
                rating_category = "مقبول"
            elif 75.0 < ratio <= 85.0:
                rating_category = "جيد"
            else:
                rating_category = "مكافح"

            raw_eval_list.append({
                "user_id": u['user_id'],
                "الموظف": u['full_name'],
                "المجموعة": u['role_group'],
                "النقاط المكتسبة": pts['earned'],
                "الخصومات والتأخير": pts['deducted'],
                "صافي التقييم": net,
                "النسبة المئوية": f"{ratio:.1f}%",
                "التصنيف": rating_category,
                "عدد الشركات (ثابت)": len(emp_companies),
                "قائمة الشركات": emp_companies,
                "ملاحظات المدير": pts['notes']
            })

        df_eval = pd.DataFrame(raw_eval_list)

        if filter_emp != "الكل":
            df_eval = df_eval[df_eval["الموظف"] == filter_emp]

        if filter_rank == "الأعلى تقييماً (Top Performers)":
            df_eval = df_eval.sort_values(by="صافي التقييم", ascending=False)
        elif filter_rank == "الأقل تقييماً (Lowest Performers)":
            df_eval = df_eval.sort_values(by="صافي التقييم", ascending=True)

        df_eval.reset_index(drop=True, inplace=True)
        df_eval.index = df_eval.index + 1
        df_eval.index.name = "#"

        st.markdown("#### 📋 جدول التقييم العام للموظفين")
        display_df = df_eval.drop(columns=["user_id", "قائمة الشركات"])
        st.dataframe(display_df, use_container_width=True)

        col_ex1, col_ex2 = st.columns([2, 2])
        with col_ex1:
            csv_data = display_df.to_csv(index=True).encode('utf-8-sig')
            st.download_button("📥 تصدير التقرير (Excel / CSV)", data=csv_data, file_name="Performance_Report.csv", mime="text/csv", use_container_width=True)
        
        with col_ex2:
            if st.button("🔄 إعادة التقييمات للوضع السابق", use_container_width=True):
                st.session_state['user_points'] = {k: v.copy() for k, v in st.session_state['initial_user_points'].items()}
                st.success("✅ تم إعادة التقييمات للنظام السابق بنجاح!")
                st.rerun()

        st.write("---")

        # --- قسم الكارت التعريفي المزدوج الوجهين ---
        st.markdown("### 💳 كارت الموظف المزدوج (Canva Modern Business ID Card)")
        selected_card_emp = st.selectbox("اختر الموظف", [u['full_name'] for u in active_users_eval])
        card_user_data = next((item for item in raw_eval_list if item['الموظف'] == selected_card_emp), None)

        if card_user_data:
            u_id = card_user_data['user_id']

            # لوحة تعديل النقاط والملاحظات والصورة
            with st.expander(f"✏️ تعديل النقاط وملاحظات المدير وصورة الموظف لـ ({selected_card_emp})"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_earned = st.number_input("تعديل النقاط المكتسبة:", min_value=0, value=card_user_data['النقاط المكتسبة'], key=f"e_ear_{u_id}")
                    edit_deducted = st.number_input("تعديل الخصومات والتأخيرات:", min_value=0, value=card_user_data['الخصومات والتأخير'], key=f"e_ded_{u_id}")
                    edit_admin_notes = st.text_area("ملاحظات المدير الإدارية:", value=card_user_data['ملاحظات المدير'], height=80, key=f"e_not_{u_id}")

                with col_e2:
                    st.markdown("**🖼️ إدارة صورة الموظف:**")
                    uploaded_img = st.file_uploader("1. رفع صورة مباشرة:", type=["jpg", "png", "jpeg"], key=f"up_img_{u_id}")
                    if uploaded_img:
                        st.session_state['user_photos'][u_id] = uploaded_img.getvalue()

                    st.markdown("---")
                    st.markdown("**2. رابط صورة الذكاء الاصطناعي المحدثة:**")
                    ai_img_url = st.text_input("رابط صورة الـ AI:", value="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&auto=format&fit=crop", key=f"ai_url_{u_id}")
                    
                    if st.button("✅ اعتماد هذه الصورة للـ AI للكارت", key=f"btn_confirm_ai_{u_id}"):
                        st.session_state['user_photos'][u_id] = ai_img_url
                        st.success("🎉 تم اعتماد وتحديث صورة الكارت بنجاح!")
                        st.rerun()

                if st.button("💾 حفظ واعتماد كل التعديلات نهائياً", key=f"btn_save_eval_{u_id}"):
                    st.session_state['user_points'][u_id] = {
                        "earned": edit_earned,
                        "deducted": edit_deducted,
                        "notes": edit_admin_notes.strip()
                    }
                    st.success("✅ تم حفظ التعديلات بنجاح!")
                    st.rerun()

            st.write("---")

            # تصدير الكارت إلى ملف PDF صفحة واحدة
            pdf_html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 2px solid #8c6d58; border-radius: 10px; background-color: #fdfbf7;">
                <h1 style="color:#4e342e; text-align:center;">Mohamed Salem OPS App - Official ID Card</h1>
                <hr style="border-color: #8c6d58;">
                <h2>📇 الموظف: {card_user_data['الموظف']} (ID: #{u_id})</h2>
                <p><strong>المجموعة:</strong> {card_user_data['المجموعة']}</p>
                <p><strong>صافي التقييم الفعلي:</strong> {card_user_data['صافي التقييم']} نقطة ({card_user_data['التصنيف']} - {card_user_data['النسبة المئوية']})</p>
                <p><strong>ملاحظات المدير:</strong> {card_user_data['ملاحظات المدير']}</p>
                <p><strong>عدد الشركات المسندة:</strong> {card_user_data['عدد الشركات (ثابت)']} شركة</p>
            </div>
            """
            
            st.download_button(
                label="📄 إصدار وتصدير الكارت كاملاً كملف (PDF) في صفحة واحدة",
                data=pdf_html_content.encode('utf-8-sig'),
                file_name=f"ID_Card_{card_user_data['الموظف']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            st.write("---")
            st.markdown("#### 📄 الوجه الأول: البيانات الشخصية والصورة")
            
            # 1. عرض الوجه الأول للكارت
            col_c1, col_c2 = st.columns([1, 2])
            with col_c1:
                photo_data = st.session_state['user_photos'].get(u_id)
                if photo_data:
                    st.image(photo_data, width=200, caption=card_user_data['الموظف'])
                else:
                    st.markdown("<div style='width:200px; height:200px; background-color:#8c6d58; color:white; display:flex; align-items:center; justify-content:center; border-radius:16px; font-size:70px;'>👤</div>", unsafe_allow_html=True)

            with col_c2:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdfbf7 0%, #d7c4b7 100%); border: 3px solid #8c6d58; border-radius: 16px; padding: 20px; color: #3e2723; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #8c6d58; padding-bottom: 8px;">
                        <h2 style="margin:0; color: #4e342e;">📇 {card_user_data['الموظف']}</h2>
                        <span style="background-color: #4e342e; color: white; padding: 4px 12px; border-radius: 12px; font-weight:bold;">ID: #{u_id}</span>
                    </div>
                    <p style="margin-top:12px; font-size:22px !important;">المجموعة الصلاحية: <strong>{card_user_data['المجموعة']}</strong></p>
                    <p style="font-size:20px !important;">التخصص: <strong>عمليات الشحن واللوجستيات (OPS Freight)</strong></p>
                    <p style="font-size:20px !important; color:#8c6d58;"><strong>Mohamed Salem OPS App Official ID</strong></p>
                </div>
                """, unsafe_allow_html=True)

            st.write("---")
            st.markdown("#### 📊 الوجه الثاني: تقييم الأداء والشركات القائم عليها")

            # 2. عرض الوجه الثاني للكارت
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffffff 0%, #f1e8e1 100%); border: 3px solid #8c6d58; border-radius: 16px; padding: 20px; color: #3e2723; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">
                <h3 style="margin:0; color: #4e342e; border-bottom: 2px solid #8c6d58; padding-bottom: 8px;">📊 ملخص تقييم أداء الموظف</h3>
                <p style="margin-top:12px;"><strong>🏆 صافي التقييم الفعلي:</strong> <span style="font-size: 28px !important; color: #4e342e; font-weight: bold;">{card_user_data['صافي التقييم']} نقطة</span> (التصنيف: <span style="background-color:#8c6d58; color:white; padding: 2px 8px; border-radius: 6px;">"{card_user_data['التصنيف']}"</span> - بنسبة {card_user_data['النسبة المئوية']})</p>
                <p><strong>📝 ملاحظات المدير:</strong> {card_user_data['ملاحظات المدير']}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"#### 🏢 الشركات والعملاء القائم عليها الموظف (العدد الإجمالي الثابت: {card_user_data['عدد الشركات (ثابت)']} شركة):")
            if card_user_data['قائمة الشركات']:
                df_comp = pd.DataFrame([{"#": idx+1, "اسم الشركة / العميل": comp} for idx, comp in enumerate(card_user_data['قائمة الشركات'])])
                st.dataframe(df_comp, use_container_width=True)
            else:
                st.info("لا توجد شركات مسجلة على هذا الموظف حالياً.")
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