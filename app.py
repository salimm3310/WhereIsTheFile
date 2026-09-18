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
    page_title="فين الملف؟ - U.S.C Logistics",
    page_icon="📂",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #0f172a; }
    .main-header { text-align: center; color: #1e3a8a; font-weight: 800; font-size: 32px; margin-bottom: 2px; }
    .sub-header { text-align: center; color: #475569; font-size: 15px; margin-bottom: 25px; }
    .stButton>button { width: 100%; background-color: #2563eb; color: white; border-radius: 6px; font-weight: bold; border: none; padding: 8px; }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
    .status-badge-ontime { background-color: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .status-badge-alert { background-color: #fef9c3; color: #854d0e; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .status-badge-late { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .chat-bubble-in { background-color: #ffffff; border-right: 4px solid #2563eb; padding: 10px; border-radius: 6px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def format_whatsapp_phone(raw_phone, default_country_code="20"):
    clean_phone = re.sub(r'[^\d]', '', str(raw_phone).strip())
    if clean_phone.startswith('00'): clean_phone = clean_phone[2:]
    if clean_phone.startswith('01') and len(clean_phone) == 11: clean_phone = default_country_code + clean_phone[1:]
    return clean_phone

def parse_reference_string(raw_text):
    parts = [p.strip() for p in raw_text.split(' - ') if p.strip() != '']
    if len(parts) >= 8:
        po_num = parts[0]
        file_num = parts[1]
        c_count = 1
        cont_raw = parts[2]
        count_match = re.search(r'(\d+(\.\d+)?)', cont_raw)
        if count_match:
            try: c_count = int(float(count_match.group(1)))
            except: c_count = 1
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
            company_val = parts[company_idx] if company_idx < len(parts) else ''
            bkg_val = parts[company_idx + 1] if company_idx + 1 < len(parts) else ''
            item_desc_val = " - ".join(parts[company_idx + 2:]) if company_idx + 2 < len(parts) else ''
        else:
            inv_clean = parts[6]
            company_val = parts[7] if len(parts) > 7 else ''
            bkg_val = parts[8] if len(parts) > 8 else ''
            item_desc_val = " - ".join(parts[9:]) if len(parts) > 9 else ''

        return {
            'po_number': po_num, 'file_number': file_num, 'container_count': c_count,
            'container_type': c_type, 'pol': pol_val, 'pod': pod_val,
            'destination_country': dest_country, 'invoice_number': inv_clean,
            'company_name': company_val, 'booking_number': bkg_val, 'item_description': item_desc_val
        }, True
    return None, False

def calculate_sla_status(current_status, last_updated_at):
    if not last_updated_at: return "في الموعد (On Time)", "status-badge-ontime", 0
    return "في الموعد (On Time)", "status-badge-ontime", 12.5

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = True
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {'user_id': 1, 'full_name': 'SALEM Admin', 'phone_number': '01212231815', 'role_group': 'Admin'}

st.markdown("<h1 style='text-align: center; color: #2563eb;'>📦 تطبيق فين الملف؟</h1>", unsafe_allow_html=True)
st.markdown("<h1 class='main-header'>U.S.C Logistics Operation Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>نظام إدارة وتتبع اللوجستيات والمراسلات وتقييم الأداء SLA - SALEM Management</p>", unsafe_allow_html=True)

if st.session_state['logged_in']:
    user = st.session_state['user_info']
    col_u, col_l = st.columns([4, 1])
    with col_u: st.success(f"👤 الموظف: **{user['full_name']}** | المجموعة: **{user['role_group']}**")
    with col_l:
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
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

    # 1. لوحة التحليلات المتقدمة
    if choice == "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)":
        st.subheader("📈 لوحة التحليلات المتقدمة والشاملة (Comprehensive Analytics)")
        mock_shipments = pd.DataFrame([
            {"shipment_id": 1, "file_number": "260862115", "company_name": "U.S.C", "invoice_number": "3A - 3B", "current_status": "Under Operation", "is_holded": 0, "last_updated_at": "2026-09-18 10:00:00", "full_name": "SALEM Admin", "user_id": 1},
            {"shipment_id": 2, "file_number": "260862116", "company_name": "CFA Global", "invoice_number": "104B", "current_status": "Waiting BL", "is_holded": 0, "last_updated_at": "2026-09-18 11:30:00", "full_name": "أحمد علي", "user_id": 2},
            {"shipment_id": 3, "file_number": "260862117", "company_name": "Al-Salem Trading", "invoice_number": "88C", "current_status": "Ready to be invoiced", "is_holded": 0, "last_updated_at": "2026-09-18 12:15:00", "full_name": "SALEM Admin", "user_id": 1},
            {"shipment_id": 4, "file_number": "260862118", "company_name": "U.S.C", "invoice_number": "99A", "current_status": "Draft", "is_holded": 1, "last_updated_at": "2026-09-18 09:00:00", "full_name": "محمود حسن", "user_id": 3}
        ])

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            all_emp = ["كل الموظفين (الشامل)"] + list(mock_shipments["full_name"].unique())
            sel_emp = st.selectbox("👤 اختر الموظف المحدد أو كافة الموظفين:", all_emp)
        with col_f2:
            analysis_opts = [
                "📊 تقييم وأداء الموظف (1 نقطة/شحنة)",
                "🏢 تقييم أداء العميل",
                "🔄 عدد الشحنات بالحالات الخاصة بها",
                "🎯 أكثر حالة مكررة للموظف",
                "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)"
            ]
            sel_analysis = st.selectbox("💡 اختر التحليل المطلوب إظهاره:", analysis_opts)

        st.write("---")
        filtered_df = mock_shipments if sel_emp == "كل الموظفين (الشامل)" else mock_shipments[mock_shipments["full_name"] == sel_emp]

        if sel_analysis == "📊 تقييم وأداء الموظف (1 نقطة/شحنة)":
            st.markdown(f"### 📊 تقييم وأداء الموظف: **{sel_emp}**")
            total_s = len(filtered_df)
            net_points = total_s * 1  # القاعدة المعتمدة: 1 نقطة لكل شحنة
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("📦 إجمالي الشحنات", f"{total_s} شحنات")
            k2.metric("➕ النقاط المكتسبة (+1 نقطة)", f"+{net_points} نقطة")
            k3.metric("➖ الخصومات والتأخير", "0 نقطة")
            k4.metric("🏆 التقييم الفعلي النهائي", f"{net_points} نقطة")

            fig1 = px.bar(filtered_df["current_status"].value_counts().reset_index(), x="current_status", y="count", color="current_status", title="توزيع الشحنات حسب الحالة", text_auto=True)
            st.plotly_chart(fig1, use_container_width=True)

        elif sel_analysis == "🏢 تقييم أداء العميل":
            fig2 = px.bar(filtered_df.groupby("company_name").size().reset_index(name="العدد"), x="company_name", y="العدد", color="company_name", title="إجمالي شحنات العملاء", text_auto=True)
            st.plotly_chart(fig2, use_container_width=True)

        elif sel_analysis == "🔄 عدد الشحنات بالحالات الخاصة بها":
            fig3 = px.pie(filtered_df, names="current_status", hole=0.3, title="نسب الحالات التشغيلية")
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("#### 📋 جدول الشحنات التفصيلي")
        st.dataframe(filtered_df, use_container_width=True)

    # 2. إدارة الحالات والتتبع
    elif choice == "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)":
        st.subheader("🔄 شاشة إدارة الحالات وتتبع المهل الزمني")
        st.info("💡 يمكنك تحديد الشحنة، تغيير حالتها بين الحالات الـ 8 وتفعيل التعليق Hold/Resume.")

    # 3. إضافة شحنة جديدة
    elif choice == "➕ إضافة شحنة جديدة (تفكيك الـ 11)":
        st.subheader("📋 تفكيك السطر المرجعي وإدخال الشحنة")
        raw_ref = st.text_area("ألصق السطر المرجعي هنا (11 حقل):", value="C - 260862115 - 4.0 x 40 RFH - PSD - LATTAKIA - Syria - INV 3A - 3B - U.S.C لحد دلوقتى - CFA0951367")
        if st.button("🔍 تفكيك البيانات وتعبئة الحقول"):
            parsed, ok = parse_reference_string(raw_ref)
            if ok:
                st.success("✅ تم تفكيك السطر المرجعي بنجاح!")
                st.json(parsed)

    # 4. المراسلات والواتساب
    elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
        st.subheader("💬 المراسلات المباشرة والتكامل مع WhatsApp")
        phone_no = st.text_input("رقم الواتساب للعميل:", value="01212231815")
        msg_val = st.text_area("نص الرسالة التلقائي:", value="مرحباً، تحديث جديد لشحنتكم ملف (260862115) - الحالة: Under Operation")
        if phone_no:
            url_wa = f"https://wa.me/2{format_whatsapp_phone(phone_no)}?text={urllib.parse.quote(msg_val)}"
            st.link_button("🟢 فتح شات الرقم المباشر في WhatsApp", url_wa)

    # 5. تقارير تقييم الأداء
    elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
        st.subheader("📊 تقارير الأداء والمكافآت المعتمدة (1 نقطة = 1 شحنة)")
        st.success("✅ معادلة التقييم المعتمدة والمطبقة بالنظام: 1 نقطة لكل شحنة منجزة بنجاح.")

    # 6. سجل الحالات والتدقيق
    elif choice == "📋 سجل الحالات والتدقيق (Status Logs)":
        st.subheader("📋 سجل التدقيق والتغييرات التاريخية (Status Logs)")
        st.dataframe(pd.DataFrame([
            {"#": 1, "الشحنة": "260862115", "الحالة السابقة": "Draft", "الحالة الجديدة": "Under Operation", "التاريخ": "2026-09-18 10:00:00"},
            {"#": 2, "الشحنة": "260862116", "الحالة السابقة": "Under Operation", "الحالة الجديدة": "Waiting BL", "التاريخ": "2026-09-18 11:30:00"}
        ]), use_container_width=True)

    # 7. لوحة التحكم الإدارية
    elif choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
        st.subheader("⚙️ لوحة التحكم الإدارية الصلاحيات وSLA")
        st.success("أهلاً بك يا مدير النظام SALEM! جميع الصلاحيات مفعلة بكفاءة 100%.")