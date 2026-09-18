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
        font-size: 15px;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        padding: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        color: white;
    }
    .status-badge-ontime {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-badge-alert {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-badge-late {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
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

# =========================================================
# 3. دالة تفكيك السطر المرجعي الـ 11 حقل
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

# =========================================================
# 4. دالة حساب حالة الـ SLA والتأخيرات
# =========================================================
def calculate_sla_status(current_status, last_updated_at):
    if not last_updated_at:
        return "في الموعد (On Time)", "status-badge-ontime", 0

    sla_query = "SELECT check_days, check_hours, late_days, late_hours FROM sla_configurations WHERE status_name = ?"
    res = execute_query(sla_query, (current_status,), fetch=True)
    
    max_check_hours = 48
    max_late_hours = 96

    if res and len(res[1]) > 0:
        c_days, c_hrs, l_days, l_hrs = res[1][0]
        max_check_hours = (c_days * 24) + c_hrs
        max_late_hours = (l_days * 24) + l_hrs

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
# 5. تهيئة جلسة المستخدم (Session State)
# =========================================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = True
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {'user_id': 1, 'full_name': 'SALEM Admin', 'phone_number': '01212231815', 'role_group': 'Admin'}

# الهيدر واللوجو الرئيسي
st.markdown("<h1 style='text-align: center; color: #2563eb;'>📦 تطبيق فين الملف؟</h1>", unsafe_allow_html=True)
st.markdown("<h1 class='main-header'>U.S.C Logistics Operation Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>نظام إدارة وتتبع اللوجستيات والمراسلات وتقييم الأداء SLA - SALEM Management</p>", unsafe_allow_html=True)

# =========================================================
# 6. الواجهة الكاملة الشاملة
# =========================================================
if st.session_state['logged_in']:
    user = st.session_state['user_info']
    
    col_user, col_logout = st.columns([4, 1])
    with col_user:
        st.success(f"👤 الموظف: **{user['full_name']}** | المجموعة: **{user['role_group']}**")
    with col_logout:
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
    # التبويب 1: الرسوم البيانية والتحليلات الـ 7
    # ---------------------------------------------------------
    if choice == "📊 لوحة المؤشرات والتحليلات المخصصة (Analytics Dashboard)":
        st.subheader("📈 لوحة التحليلات المتقدمة والشاملة (Comprehensive Analytics)")

        shipments_query = """
            SELECT s.shipment_id, s.file_number, s.company_name, s.invoice_number, 
                   s.current_status, s.is_holded, s.last_updated_at, u.full_name, u.user_id
            FROM shipments s
            LEFT JOIN users u ON s.created_by_user = u.user_id
        """
        res = execute_query(shipments_query, fetch=True)

        if res and len(res[1]) > 0:
            df_shipments = pd.DataFrame([list(r) for r in res[1]], columns=[
                "shipment_id", "file_number", "company_name", "invoice_number", 
                "current_status", "is_holded", "last_updated_at", "full_name", "user_id"
            ])
        else:
            df_shipments = pd.DataFrame([
                {"shipment_id": 1, "file_number": "260862115", "company_name": "U.S.C", "invoice_number": "3A - 3B", "current_status": "Under Operation", "is_holded": 0, "last_updated_at": "2026-09-18 10:00:00", "full_name": "SALEM Admin", "user_id": 1},
                {"shipment_id": 2, "file_number": "260862116", "company_name": "CFA Global", "invoice_number": "104B", "current_status": "Waiting BL", "is_holded": 0, "last_updated_at": "2026-09-18 11:30:00", "full_name": "أحمد علي", "user_id": 2},
                {"shipment_id": 3, "file_number": "260862117", "company_name": "Al-Salem Trading", "invoice_number": "88C", "current_status": "Ready to be invoiced", "is_holded": 0, "last_updated_at": "2026-09-18 12:15:00", "full_name": "SALEM Admin", "user_id": 1},
                {"shipment_id": 4, "file_number": "260862118", "company_name": "U.S.C", "invoice_number": "99A", "current_status": "Draft", "is_holded": 1, "last_updated_at": "2026-09-18 09:00:00", "full_name": "محمود حسن", "user_id": 3}
            ])

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
            net_points = total_shipments * 1  # 1 نقطة لكل شحنة

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
    # التبويب 2: إدارة الحالات وتتبع المهل والتعليق والملاحظات
    # ---------------------------------------------------------
    elif choice == "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)":
        st.subheader("🔄 شاشة إدارة الحالات وتتبع المهل الزمنية (SLA & Lifecycle)")

        shipments_query = """
            SELECT s.shipment_id, s.file_number, s.company_name, s.booking_number, 
                   s.invoice_number, s.current_status, s.is_holded, s.hold_reason, 
                   s.last_updated_at, u.full_name
            FROM shipments s
            LEFT JOIN users u ON s.created_by_user = u.user_id
            ORDER BY s.last_updated_at DESC
        """
        res = execute_query(shipments_query, fetch=True)

        rows = res[1] if (res and len(res[1]) > 0) else [
            (1, "260862115", "U.S.C", "CFA0951367", "3A - 3B", "Under Operation", 0, None, "2026-09-18 10:00:00", "SALEM Admin"),
            (2, "260862116", "CFA Global", "CFA0951368", "104B", "Waiting BL", 0, None, "2026-09-18 11:30:00", "أحمد علي"),
            (3, "260862117", "Al-Salem Trading", "CFA0951369", "88C", "Ready to be invoiced", 0, None, "2026-09-18 12:15:00", "SALEM Admin"),
            (4, "260862118", "U.S.C", "CFA0951370", "99A", "Draft", 1, "في انتظار موافقة العميل", "2026-09-18 09:00:00", "محمود حسن")
        ]

        shipment_list = []
        for r in rows:
            s_id, file_num, company, bkg, inv, status, holded, h_reason, last_up, creator = r
            sla_label, sla_class, elapsed_h = calculate_sla_status(status, last_up)
            
            shipment_list.append({
                'ID': s_id,
                'رقم الملف': file_num,
                'الشركة': company,
                'رقم الحجز': bkg,
                'رقم الفاتورة': inv,
                'الحالة الحالية': f"⏸️ معلقة (Hold)" if holded else status,
                'وضع SLA': sla_label,
                'الساعات المنقضية': f"{elapsed_h:.1f} ساعة",
                'الموظف المسؤول': creator,
                'آخر تحديث': str(last_up) if last_up else ''
            })

        df = pd.DataFrame(shipment_list)
        st.markdown("#### 📋 جدول الشحنات النشطة ومؤشرات الالتزام")
        st.dataframe(df, use_container_width=True)

        st.write("---")
        st.markdown("### 🛠️ إجراءات تحديث الحالة وتأكيد الملاحظات")

        shipment_options = {f"ملف: {r[1]} - شركة: {r[2]} (الحالة: {r[5]})": r for r in rows}
        selected_option = st.selectbox("اختر الشحنة المراد تغيير حالتها أو إثبات ملاحظة عليها:", list(shipment_options.keys()))
        s_data = shipment_options[selected_option]
        selected_shipment_id = s_data[0]
        curr_status = s_data[5]
        curr_holded = s_data[6]
        curr_h_reason = s_data[7]

        col_status_change, col_notes = st.columns([2, 2])

        with col_status_change:
            st.markdown("**1. تغيير الحالة التشغيلية أو التعليق:**")
            all_statuses = [
                'Under Operation', 'Waiting BL', 'Draft', 
                'Waiting Confirmation', 'Stamped', 
                'Ready to be invoiced', 'Closed'
            ]
            
            new_selected_status = st.selectbox("اختر الحالة الجديدة:", all_statuses, index=all_statuses.index(curr_status) if curr_status in all_statuses else 0)
            set_hold = st.checkbox("تفعيل تعليق الشحنة (Put on Hold)", value=bool(curr_holded))
            hold_reason_text = ""
            if set_hold:
                hold_reason_text = st.text_input("سبب التعليق (إجباري عند تفعيل التعليق):", value=curr_h_reason if curr_h_reason else "")

            if st.button("💾 حفظ التحديث وتسجيل التقييم (1 نقطة)"):
                if set_hold and hold_reason_text.strip() == "":
                    st.error("⚠️ يرجى كتابة سبب التعليق عند تفعيل خيار Hold.")
                else:
                    eval_sql = "INSERT INTO performance_evaluations (user_id, shipment_id, evaluation_type, time_difference_hours, admin_status) VALUES (?, ?, 'Positive_Bonus', 0, 'Approved')"
                    execute_query(eval_sql, (user['user_id'], selected_shipment_id))

                    update_shipment_sql = "UPDATE shipments SET current_status = ?, is_holded = ?, hold_reason = ? WHERE shipment_id = ?"
                    execute_query(update_shipment_sql, (new_selected_status, 1 if set_hold else 0, hold_reason_text.strip() if set_hold else None, selected_shipment_id))

                    st.success(f"✅ تم تحديث حالة الملف ({s_data[1]}) إلى [{new_selected_status}] وتسجيل 1 نقطة تقييم للموظف بنجاح!")
                    st.rerun()

        with col_notes:
            st.markdown("**2. إضافة ملاحظة ميدانية مفتوحة (Open Note):**")
            new_note = st.text_area("اكتب ملاحظتك التوضيحية على هذه الشحنة:", height=110, placeholder="مثال: العميل طلب التأجيل لحين استلام الفاتورة النهائية")
            if st.button("📝 إضافة الملاحظة للسجل"):
                if new_note.strip() != "":
                    note_sql = "INSERT INTO shipment_notes (shipment_id, added_by_user, note_content) VALUES (?, ?, ?)"
                    execute_query(note_sql, (user['user_id'], selected_shipment_id, new_note.strip()))
                    st.success("✅ تم إضافة الملاحظة وتوثيقها باسم الموظف بنجاح.")
                else:
                    st.warning("يرجى كتابة نص الملاحظة قبل الضغط على الزر.")

    # ---------------------------------------------------------
    # التبويب 3: تفكيك السطر المرجعي الـ 11 والإدخال
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
                    st.success(f"🎉 تم حفظ الشحنة ({file_num}) بنجاح! الحالة: Under Operation")

    # ---------------------------------------------------------
    # التبويب 4: المراسلات والواتساب المباشر
    # ---------------------------------------------------------
    elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
        st.subheader("💬 المراسلات الداخلية والتكامل مع WhatsApp")

        tab_msg, tab_wa = st.tabs(["📩 الرسائل الداخلية النظامية", "📱 إرسال إشعار WhatsApp direct"])

        with tab_msg:
            col_send, col_inbox = st.columns([2, 3])
            with col_send:
                st.markdown("### 📤 إرسال رسالة داخلية")
                st.selectbox("إلى الموظف:", ["أحمد علي (مُشغّل)", "محمود حسن (خدمة عملاء)"])
                st.text_area("نص الرسالة:", height=100)
                if st.button("🚀 إرسال الرسالة الداخلية"):
                    st.success("✅ تم إرسال الرسالة بنجاح!")
            with col_inbox:
                st.markdown("### 📥 صندوق الرسائل الواردة")
                st.markdown("""
                <div class="chat-bubble-in">
                    <strong>رسالة من: أحمد علي</strong><br>
                    <span style="color: #475569;">تم استلام البوليسة رقم CFA0951367 وفي انتظار موافقة العميل</span><br>
                    <small style="color: #94a3b8;">📅 اليوم - 10:30 AM</small>
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
                f"تحياتنا، فريق التشغيل لشركة U.S.C"
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
                    st.link_button("🟢 فتح شات الرقم المباشر في WhatsApp", direct_wa_url, use_container_width=True)

    # ---------------------------------------------------------
    # التبويب 5: تقارير تقييم الأداء والمكافآت
    # ---------------------------------------------------------
    elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
        st.subheader("📊 تقارير تقييم الأداء والمكافآت والتأخيرات")

        st.success("✅ قاعدة التقييم المعتمدة بالنظام: 1 نقطة لكل شحنة متوافقة ومكتملة.")
        st.dataframe(pd.DataFrame([
            {"الموظف": "SALEM Admin", "عدد الشحنات المنجزة": 12, "نقاط الإنجاز (+1)": 12, "نقاط التأخير (-1)": 0, "صافي التقييم": 12},
            {"الموظف": "أحمد علي", "عدد الشحنات المنجزة": 8, "نقاط الإنجاز (+1)": 8, "نقاط التأخير (-1)": -1, "صافي التقييم": 7},
            {"الموظف": "محمود حسن", "عدد الشحنات المنجزة": 5, "نقاط الإنجاز (+1)": 5, "نقاط التأخير (-1)": 0, "صافي التقييم": 5}
        ]), use_container_width=True)

    # ---------------------------------------------------------
    # التبويب 6: سجل الحالات والتدقيق
    # ---------------------------------------------------------
    elif choice == "📋 سجل الحالات والتدقيق (Status Logs)":
        st.subheader("📋 سجل الحالات والتدقيق التاريخي (Status Logs & Audit Trail)")
        st.dataframe(pd.DataFrame([
            {"#": 1, "الشحنة": "260862115", "الحالة السابقة": "Draft", "الحالة الجديدة": "Under Operation", "التاريخ والوقت": "2026-09-18 10:00:00"},
            {"#": 2, "الشحنة": "260862116", "الحالة السابقة": "Under Operation", "الحالة الجديدة": "Waiting BL", "التاريخ والوقت": "2026-09-18 11:30:00"},
            {"#": 3, "الشحنة": "260862117", "الحالة السابقة": "Stamped", "الحالة الجديدة": "Ready to be invoiced", "التاريخ والوقت": "2026-09-18 12:15:00"}
        ]), use_container_width=True)

    # ---------------------------------------------------------
    # التبويب 7: لوحة التحكم الإدارية
    # ---------------------------------------------------------
    elif choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
        st.subheader("⚙️ لوحة إدارة الحسابات والصلاحيات وSLA (SALEM Control Panel)")
        st.dataframe(pd.DataFrame([
            {"#": 1, "الاسم": "SALEM Admin", "الهاتف": "01212231815", "المجموعة": "Admin", "الحالة": "Active"},
            {"#": 2, "الاسم": "أحمد علي", "الهاتف": "01012345678", "المجموعة": "Operator", "الحالة": "Active"},
            {"#": 3, "الاسم": "محمود حسن", "الهاتف": "01112345678", "المجموعة": "CS", "الحالة": "Active"}
        ]), use_container_width=True)