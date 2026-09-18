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
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

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
            if inv_index + 1 < len(parts) and len(parts[inv_index+1]) <= 10 and not any(char.isdigit() for char in parts[inv_index+1]) == False:
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
        return "غير محدد", "status-badge-ontime", 0

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
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# الهيدر واللوجو الرئيسي
st.markdown("<h1 style='text-align: center; color: #2563eb;'>📦 تطبيق فين الملف؟</h1>", unsafe_allow_html=True)
st.markdown("<h1 class='main-header'>U.S.C Logistics Operation Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>نظام إدارة وتتبع اللوجستيات والمراسلات وتقييم الأداء SLA - SALEM Management</p>", unsafe_allow_html=True)

# =========================================================
# 6. الواجهة الكاملة بعد تسجيل الدخول
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
    # شاشة الرسوم البيانية والتحليلات المقترحة الشاملة
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
            df_shipments["full_name"] = df_shipments["full_name"].fillna("غير محدد")

            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                all_employees = ["كل الموظفين (الشامل)"] + list(df_shipments["full_name"].unique())
                selected_emp = st.selectbox("👤 1️⃣ اختر الموظف المحدد أو كافة الموظفين:", all_employees)

            if selected_emp != "كل الموظفين (الشامل)":
                filtered_df = df_shipments[df_shipments["full_name"] == selected_emp]
            else:
                filtered_df = df_shipments.copy()

            with col_filter2:
                analysis_options = [
                    "📊 تقييم وأداء الموظف",
                    "🏢 تقييم أداء العميل",
                    "🔄 عدد الشحنات بالحالات الخاصة بها",
                    "🎯 أكثر حالة مكررة للموظف",
                    "🏷️ أكثر حالة مكررة لاسم عميل محدد",
                    "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)",
                    "📂 استعلام ملفات العملاء المجمعة"
                ]
                selected_analysis = st.selectbox("💡 2️⃣ اختر التحليل المطلوب إظهاره:", analysis_options)

            st.write("---")

            # 1. تقييم وأداء الموظف (1 نقطة لكل شحنة)
            if selected_analysis == "📊 تقييم وأداء الموظف":
                st.markdown(f"### 📊 تقييم وأداء الموظف: **{selected_emp}**")

                if selected_emp != "كل الموظفين (الشامل)":
                    target_user_id = filtered_df["user_id"].iloc[0] if not filtered_df.empty else None
                    eval_sql = """
                        SELECT evaluation_type, COUNT(*) 
                        FROM performance_evaluations 
                        WHERE user_id = ? AND admin_status = 'Approved'
                        GROUP BY evaluation_type
                    """
                    eval_res = execute_query(eval_sql, (target_user_id,), fetch=True) if target_user_id else None
                else:
                    eval_sql = """
                        SELECT evaluation_type, COUNT(*) 
                        FROM performance_evaluations 
                        WHERE admin_status = 'Approved'
                        GROUP BY evaluation_type
                    """
                    eval_res = execute_query(eval_sql, fetch=True)

                bonus_count = 0
                late_count = 0

                if eval_res and len(eval_res[1]) > 0:
                    for ev_row in eval_res[1]:
                        if ev_row[0] == 'Positive_Bonus':
                            bonus_count = ev_row[1]
                        elif ev_row[0] == 'Negative_Late':
                            late_count = ev_row[1]

                net_score = (bonus_count * 1) - (late_count * 1)

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("📦 إجمالي الشحنات", len(filtered_df))
                k2.metric("➕ النقاط الإضافية (+1 نقطة)", f"+{bonus_count * 1} نقطة", f"{bonus_count} عملية سرعة")
                k3.metric("➖ النقاط المخصومة (-1 نقطة)", f"-{late_count * 1} نقطة", f"{late_count} حالة تأخير")
                k4.metric("🏆 التقييم الفعلي النهائي", f"{net_score} نقطة")

                st.write("---")
                st.markdown("#### 📈 توزيع شحنات الموظف حسب الحالة التشغيلية")
                emp_status = filtered_df["current_status"].value_counts().reset_index()
                emp_status.columns = ["الحالة التشغيلية", "عدد الشحنات"]
                
                fig_emp_status = px.bar(emp_status, x="الحالة التشغيلية", y="عدد الشحنات", color="الحالة التشغيلية", text_auto=True)
                st.plotly_chart(fig_emp_status, use_container_width=True)

            # 2. تقييم أداء العميل
            elif selected_analysis == "🏢 تقييم أداء العميل":
                st.markdown("### 🏢 تقييم أداء وتوزيع العملاء")
                comp_summary = filtered_df.groupby("company_name").agg(
                    إجمالي_الشحنات=('shipment_id', 'count'),
                    الشحنات_المعلقة=('is_holded', 'sum')
                ).reset_index().sort_values(by="إجمالي_الشحنات", ascending=False)
                
                st.dataframe(comp_summary, use_container_width=True)
                fig_comp = px.bar(comp_summary.head(10), x="company_name", y="إجمالي_الشحنات", color="company_name", title="أعلى 10 عملاء حسماً للشحنات", text_auto=True)
                st.plotly_chart(fig_comp, use_container_width=True)

            # 3. عدد الشحنات بالحالات الخاصة بها
            elif selected_analysis == "🔄 عدد الشحنات بالحالات الخاصة بها":
                st.markdown("### 🔄 إحصائيات الشحنات حسب الحالات الـ 8")
                status_summary = filtered_df["current_status"].value_counts().reset_index()
                status_summary.columns = ["الحالة", "العدد"]
                status_summary["النسبة المئوية %"] = (status_summary["العدد"] / len(filtered_df) * 100).round(1)

                st.dataframe(status_summary, use_container_width=True)
                fig_pie_status = px.pie(status_summary, values="العدد", names="الحالة", hole=0.3, title="نسب توزيع الشحنات على الحالات الـ 8")
                st.plotly_chart(fig_pie_status, use_container_width=True)

            # 4. أكثر حالة مكررة للموظف
            elif selected_analysis == "🎯 أكثر حالة مكررة للموظف":
                st.markdown("### 🎯 الحالة الأكثر تكراراً (Bottleneck Analysis)")
                if selected_emp != "كل الموظفين (الشامل)":
                    most_common = filtered_df["current_status"].mode()
                    if not most_common.empty:
                        top_st = most_common[0]
                        st.success(f"🎯 أكثر حالة مكررة للموظف **{selected_emp}** هي: **{top_st}** (تكررت {len(filtered_df[filtered_df['current_status'] == top_st])} مرة)")
                    else:
                        st.info("لا توجد بيانات كافية.")
                else:
                    top_per_emp = df_shipments.groupby(["full_name", "current_status"]).size().reset_index(name="التكرار")
                    idx = top_per_emp.groupby("full_name")["التكرار"].idxmax()
                    result_df = top_per_emp.loc[idx].rename(columns={"full_name": "الموظف", "current_status": "أكثر حالة مكررة", "التكرار": "عدد المرات"})
                    st.dataframe(result_df, use_container_width=True)

            # 5. أكثر حالة مكررة لاسم عميل محدد
            elif selected_analysis == "🏷️ أكثر حالة مكررة لاسم عميل محدد":
                st.markdown("### 🏷️ تحليل الحالة المهيمنة لكل عميل")
                target_company = st.selectbox("اختر العميل:", filtered_df["company_name"].unique())
                comp_df = filtered_df[filtered_df["company_name"] == target_company]
                
                most_common_comp = comp_df["current_status"].mode()
                if not most_common_comp.empty:
                    st.success(f"🏷️ أكثر حالة مكررة لـ **({target_company})** هي: **{most_common_comp[0]}** (تكررت {len(comp_df[comp_df['current_status'] == most_common_comp[0]])} مرة من إجمالي {len(comp_df)} شحنة)")
                st.dataframe(comp_df[["file_number", "invoice_number", "current_status", "last_updated_at"]], use_container_width=True)

            # 6. تحليل الالتزام بالمهل الزمنية
            elif selected_analysis == "⏱️ تحليل الالتزام بالمهل الزمنية (SLA Breakdown)":
                st.markdown("### ⏱️ تحليل SLA والالتزام بالتوقيتات")
                filtered_df["sla_status"] = filtered_df.apply(
                    lambda row: calculate_sla_status(row["current_status"], row["last_updated_at"])[0], axis=1
                )
                sla_summary = filtered_df["sla_status"].value_counts().reset_index()
                sla_summary.columns = ["وضع SLA", "العدد"]
                
                fig_sla_pie = px.pie(
                    sla_summary, values="العدد", names="وضع SLA", hole=0.4,
                    color="وضع SLA",
                    color_discrete_map={
                        "في الموعد (On Time)": "#22c55e",
                        "اقتراب المهلة (Alert)": "#eab308",
                        "متأخر (Late)": "#ef4444"
                    }
                )
                st.plotly_chart(fig_sla_pie, use_container_width=True)

            # 7. استعلام ملفات العملاء المجمعة
            elif selected_analysis == "📂 استعلام ملفات العملاء المجمعة":
                st.markdown("### 📂 كشف الملفات المجمعة حسب العميل")
                selected_c = st.selectbox("اختر اسم الشركة/العميل:", filtered_df["company_name"].unique())
                c_df = filtered_df[filtered_df["company_name"] == selected_c]
                st.info(f"إجمالي الملفات المرتبطة بالعميل **({selected_c})**: **{len(c_df)}** ملف")
                st.dataframe(c_df[["file_number", "invoice_number", "current_status", "full_name", "last_updated_at"]].rename(columns={
                    "file_number": "رقم الملف",
                    "invoice_number": "رقم الفاتورة",
                    "current_status": "الحالة الحالية",
                    "full_name": "الموظف المسؤول",
                    "last_updated_at": "آخر تحديث"
                }), use_container_width=True)

        else:
            st.info("لا توجد بيانات شحنات مسجلة بالنظام حالياً.")

    # ---------------------------------------------------------
    # شاشة 1: إدارة الحالات وتتبع SLA وتحديثها
    # ---------------------------------------------------------
    elif choice == "🔄 إدارة الحالات والتتبع (Lifecycle & SLA)":
        st.subheader("🔄 شاشة إدارة الشحنات وتحديث الحالات الـ 8")

        shipments_query = """
            SELECT s.shipment_id, s.file_number, s.company_name, s.booking_number, 
                   s.invoice_number, s.current_status, s.is_holded, s.hold_reason, 
                   s.last_updated_at, u.full_name
            FROM shipments s
            LEFT JOIN users u ON s.created_by_user = u.user_id
            ORDER BY s.last_updated_at DESC
        """
        res = execute_query(shipments_query, fetch=True)

        if res and len(res[1]) > 0:
            rows = res[1]
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
                    'آخر تحديث': str(last_up) if last_up else ''
                })

            df = pd.DataFrame(shipment_list)
            st.dataframe(df, use_container_width=True)

            st.write("---")
            st.markdown("### 🛠️ تحديث حالة شحنة قائمة")

            shipment_options = {f"{r[1]} - {r[2]} (الحالة: {r[5]})": r[0] for r in rows}
            selected_option = st.selectbox("اختر الشحنة المراد تغيير حالتها:", list(shipment_options.keys()))
            selected_shipment_id = shipment_options[selected_option]

            curr_shipment_query = "SELECT current_status, is_holded, hold_reason, last_updated_at FROM shipments WHERE shipment_id = ?"
            curr_res = execute_query(curr_shipment_query, (selected_shipment_id,), fetch=True)
            curr_status, curr_holded, curr_h_reason, last_up_time = curr_res[1][0]

            col_status_change, col_notes = st.columns([2, 2])

            with col_status_change:
                st.markdown("**1. تغيير حالة الشحنة:**")
                all_statuses = [
                    'Under Operation', 'Waiting BL', 'Draft', 
                    'Waiting Confirmation', 'Stamped', 
                    'Ready to be invoiced', 'Closed'
                ]
                
                new_selected_status = st.selectbox("الحالة الجديدة:", all_statuses, index=all_statuses.index(curr_status) if curr_status in all_statuses else 0)
                
                set_hold = st.checkbox("تعليق الشحنة (Put on Hold)", value=bool(curr_holded))
                hold_reason_text = ""
                if set_hold:
                    hold_reason_text = st.text_input("سبب التعليق (إجباري عند التعليق):", value=curr_h_reason if curr_h_reason else "")

                if st.button("💾 حفظ التحديث وتسجيل السجل والتقييم"):
                    if set_hold and hold_reason_text.strip() == "":
                        st.error("⚠️ يرجى كتابة سبب التعليق عند تفعيل خيار Hold.")
                    else:
                        elapsed_h = 0.0
                        eval_type = 'Positive_Bonus'

                        eval_sql = """
                            INSERT INTO performance_evaluations (user_id, shipment_id, evaluation_type, time_difference_hours, admin_status)
                            VALUES (?, ?, ?, ?, 'Approved')
                        """
                        execute_query(eval_sql, (user['user_id'], selected_shipment_id, eval_type, elapsed_h))

                        update_shipment_sql = """
                            UPDATE shipments 
                            SET current_status = ?, is_holded = ?, hold_reason = ?
                            WHERE shipment_id = ?
                        """
                        execute_query(update_shipment_sql, (new_selected_status, 1 if set_hold else 0, hold_reason_text.strip() if set_hold else None, selected_shipment_id))

                        st.success(f"✅ تم تحديث حالة الشحنة بنجاح!")
                        st.rerun()

            with col_notes:
                st.markdown("**2. إضافة ملاحظة مفتوحة (Open Note):**")
                new_note = st.text_area("اكتب ملاحظة جديدة للشحنة:", height=100, placeholder="مثال: تم إرسال المسودة للعميل وفي انتظار التأكيد")
                if st.button("📝 إضافة الملاحظة"):
                    if new_note.strip() != "":
                        note_sql = "INSERT INTO shipment_notes (shipment_id, added_by_user, note_content) VALUES (?, ?, ?)"
                        execute_query(note_sql, (user['user_id'], selected_shipment_id, new_note.strip()))
                        st.success("✅ تم إضافة الملاحظة بنجاح.")
                    else:
                        st.warning("يرجى كتابة نص الملاحظة.")

        else:
            st.info("لا توجد شحنات في النظام حالياً.")

    # ---------------------------------------------------------
    # شاشة 2: إضافة شحنة جديدة (تفكيك الـ 11)
    # ---------------------------------------------------------
    elif choice == "➕ إضافة شحنة جديدة (تفكيك الـ 11)":
        st.subheader("📋 تفكيك السطر المرجعي وإدخال الشحنة")
        
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
                    check_query = "SELECT shipment_id FROM shipments WHERE file_number = ?"
                    exist = execute_query(check_query, (file_num.strip(),), fetch=True)
                    if exist and len(exist[1]) > 0:
                        st.error(f"❌ رقم الملف ({file_num}) مسجل بالفعل لشحنة أخرى!")
                    else:
                        insert_query = """
                            INSERT INTO shipments (
                                po_number, file_number, container_count, container_type,
                                pol, pod, destination_country, invoice_number,
                                company_name, booking_number, item_description,
                                current_status, created_by_user
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Under Operation', ?)
                        """
                        params = (
                            po_num.strip(), file_num.strip(), cont_count, cont_type.strip(),
                            pol_val.strip(), pod_val.strip(), dest_country.strip(), inv_num.strip(),
                            company.strip(), bkg_num.strip(), item_desc.strip(), user['user_id']
                        )
                        if execute_query(insert_query, params):
                            st.success(f"🎉 تم حفظ الشحنة ({file_num}) بنجاح! الحالة: Under Operation")
                            if 'parsed_data' in st.session_state:
                                del st.session_state['parsed_data']

    # ---------------------------------------------------------
    # شاشة 3: المراسلات والواتساب (Messaging & WhatsApp)
    # ---------------------------------------------------------
    elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
        st.subheader("💬 المراسلات الداخلية والتكامل مع WhatsApp")

        tab_msg, tab_wa = st.tabs(["📩 الرسائل الداخلية النظامية", "📱 إرسال إشعار WhatsApp direct"])

        with tab_msg:
            col_send, col_inbox = st.columns([2, 3])

            with col_send:
                st.markdown("### 📤 إرسال رسالة داخلية")
                users_sql = "SELECT user_id, full_name, role_group FROM users WHERE user_id != ?"
                u_res = execute_query(users_sql, (user['user_id'],), fetch=True)
                ship_sql = "SELECT shipment_id, file_number FROM shipments"
                s_res = execute_query(ship_sql, fetch=True)

                if u_res and len(u_res[1]) > 0:
                    u_options = {f"{r[1]} ({r[2]})": r[0] for r in u_res[1]}
                    target_u_id = st.selectbox("إلى الموظف:", list(u_options.keys()))
                    s_options = {"بدون شحنة محدودة": None}
                    if s_res and len(s_res[1]) > 0:
                        for s_r in s_res[1]:
                            s_options[f"ملف: {s_r[1]}"] = s_r[0]
                    target_s_id = st.selectbox("المرتبطة بشحنة (اختياري):", list(s_options.keys()))

                    msg_text = st.text_area("نص الرسالة:", height=100)

                    if st.button("🚀 إرسال الرسالة الداخلية"):
                        if msg_text.strip() != "":
                            send_sql = """
                                INSERT INTO internal_messages (sender_user_id, receiver_user_id, shipment_id, message_text)
                                VALUES (?, ?, ?, ?)
                            """
                            execute_query(send_sql, (user['user_id'], u_options[target_u_id], s_options[target_s_id], msg_text.strip()))
                            st.success("✅ تم إرسال الرسالة بنجاح!")
                        else:
                            st.warning("يرجى كتابة نص الرسالة أولاً.")

            with col_inbox:
                st.markdown("### 📥 صندوق الرسائل الواردة")
                inbox_sql = "SELECT message_id, sender_user_id, shipment_id, message_text, sent_at FROM internal_messages WHERE receiver_user_id = ?"
                inbox_res = execute_query(inbox_sql, (user['user_id'],), fetch=True)

                if inbox_res and len(inbox_res[1]) > 0:
                    for m_r in inbox_res[1]:
                        m_id, sender_id, s_id, text_val, sent_time = m_r
                        st.markdown(f"""
                        <div class="chat-bubble-in">
                            <strong>رسالة واردة</strong><br>
                            <span style="color: #475569;">{text_val}</span><br>
                            <small style="color: #94a3b8;">📅 {sent_time}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("صندوق الوارد فارغ، لا توجد رسائل واردة جديدة.")

        with tab_wa:
            st.markdown("### 📱 إرسال إشعار وتحديث عبر WhatsApp Direct")
            recipient_type = st.radio("اختر المستلم:", ["مستخدم مسجل بالنظام", "عميل/رقم خارجي"], horizontal=True)

            target_name = ""
            target_phone = ""

            if recipient_type == "مستخدم مسجل بالنظام":
                u_wa_sql = "SELECT user_id, full_name, phone_number FROM users"
                u_wa_res = execute_query(u_wa_sql, fetch=True)
                if u_wa_res and len(u_wa_res[1]) > 0:
                    u_wa_map = {f"{r[1]} ({r[2]})": (r[1], r[2]) for r in u_wa_res[1]}
                    sel_u_wa = st.selectbox("اختر المستخدم المراد مراسلته:", list(u_wa_map.keys()))
                    target_name, target_phone = u_wa_map[sel_u_wa]
            else:
                c1_wa, c2_wa = st.columns(2)
                with c1_wa:
                    target_name = st.text_input("اسم العميل/المستلم:", placeholder="مثال: أستاذ أحمد")
                with c2_wa:
                    target_phone = st.text_input("رقم الهاتف (مثال: 01012345678):", placeholder="01012345678")

            ship_sql_wa = "SELECT shipment_id, file_number, company_name, invoice_number, current_status FROM shipments"
            s_wa_res = execute_query(ship_sql_wa, fetch=True)

            template_msg_body = ""
            footer_text = "تحياتنا، فريق التشغيل لشركة U.S.C"
            
            if s_wa_res and len(s_wa_res[1]) > 0:
                s_wa_dict = {f"ملف: {r[1]} | {r[2]} | فاتورة: {r[3]}": r for r in s_wa_res[1]}
                sel_shipments = st.multiselect("اختر الشحنة أو الشحنات المراد تضمينها في الرسالة المجمعة:", list(s_wa_dict.keys()))
                greeting_header = f"مرحباً {target_name}،\n" if target_name.strip() != "" else "مرحباً،\n"
                
                if len(sel_shipments) == 1:
                    s_data = s_wa_dict[sel_shipments[0]]
                    template_msg_body = (
                        f"{greeting_header}"
                        f"تحديث جديد لشحنتكم ملف رقم ({s_data[1]})\n"
                        f"الشركة: {s_data[2]}\n"
                        f"رقم الفاتورة : {s_data[3]}\n"
                        f"الحالة الحالية: {s_data[4]}\n\n"
                        f"{footer_text}"
                    )
                elif len(sel_shipments) > 1:
                    sh_details = []
                    for idx, key in enumerate(sel_shipments, start=1):
                        s_data = s_wa_dict[key]
                        sh_details.append(
                            f"📌 الشحنة #{idx}:\n"
                            f"ملف رقم: ({s_data[1]})\n"
                            f"الشركة: {s_data[2]}\n"
                            f"رقم الفاتورة : {s_data[3]}\n"
                            f"الحالة الحالية: {s_data[4]}"
                        )
                    all_sh_str = "\n--------------------\n".join(sh_details)
                    template_msg_body = (
                        f"{greeting_header}"
                        f"تحديث جديد لشحناتكم المجمعة:\n\n"
                        f"{all_sh_str}\n\n"
                        f"{footer_text}"
                    )

            final_msg = st.text_area("معاينة نص الرسالة قبل الإرسال:", value=template_msg_body, height=220)

            if target_phone.strip() != "" and final_msg.strip() != "":
                clean_phone = format_whatsapp_phone(target_phone)
                encoded_msg = urllib.parse.quote(final_msg.strip())
                direct_wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.code(final_msg.strip(), language=None)
                    st.caption("💡 يمكنك نسخ النص بنقرة زر واحدة فوق المربع المظلل.")
                with col_b2:
                    st.info(f"📱 الرقم المعالج للإرسال: **+{clean_phone}**")
                    st.link_button("🟢 فتح شات الرقم المباشر في WhatsApp", direct_wa_url, use_container_width=True)

    # ---------------------------------------------------------
    # شاشة 4: تقارير تقييم الأداء والمكافآت
    # ---------------------------------------------------------
    elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
        st.subheader("📊 تقارير تقييم الأداء والمكافآت والتأخيرات")

        st.markdown("### 📈 إحصائيات أداء الموظفين والمكافآت المعتمدة")
        perf_summary_sql = "SELECT user_id, evaluation_type, admin_status FROM performance_evaluations"
        s_res = execute_query(perf_summary_sql, fetch=True)
        if s_res and s_res[1]:
            df_summary = pd.DataFrame([list(r) for r in s_res[1]], columns=["المستخدم", "نوع التقييم", "الحالة"])
            st.dataframe(df_summary, use_container_width=True)
        else:
            st.info("لا توجد تقييمات مسجلة بعد.")

    # ---------------------------------------------------------
    # شاشة 5: سجل الحالات والتدقيق (Status Logs)
    # ---------------------------------------------------------
    elif choice == "📋 سجل الحالات والتدقيق (Status Logs)":
        st.subheader("📋 سجل الحالات والتدقيق التاريخي (Status Logs & Audit Trail)")
        logs_query = "SELECT log_id, shipment_id, previous_status, new_status, timestamp FROM status_logs"
        logs_res = execute_query(logs_query, fetch=True)
        if logs_res and len(logs_res[1]) > 0:
            df_logs = pd.DataFrame([list(r) for r in logs_res[1]], columns=["#", "رقم الشحنة", "الحالة السابقة", "الحالة الجديدة", "التاريخ والوقت"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("سجل التدقيق فارغ حالياً.")

    # ---------------------------------------------------------
    # شاشة 6: لوحة التحكم الإدارية (Admin Panel) للمدير
    # ---------------------------------------------------------
    elif choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
        st.subheader("⚙️ لوحة إدارة الحسابات والصلاحيات وSLA (SALEM Control Panel)")
        p_res = execute_query("SELECT user_id, full_name, phone_number, role_group, account_status FROM users", fetch=True)
        if p_res and len(p_res[1]) > 0:
            df_users = pd.DataFrame([list(r) for r in p_res[1]], columns=["#", "الاسم", "الهاتف", "المجموعة", "الحالة"])
            st.dataframe(df_users, use_container_width=True)

# =========================================================
# 7. الواجهة عند عدم تسجيل الدخول (مع زر الدخول المباشر المتاح)
# =========================================================
else:
    tab_login, tab_register = st.tabs(["🔑 تسجيل الدخول", "📝 حساب جديد"])

    with tab_login:
        st.subheader("تسجيل الدخول للنظام")
        
        # زر الدخول المباشر الفوري والتلقائي لسرعة الاختبار
        if st.button("🚀 الدخول المباشر السريع للنظام (SALEM Admin)", use_container_width=True):
            st.session_state['logged_in'] = True
            st.session_state['user_info'] = {'user_id': 1, 'full_name': 'SALEM Admin', 'phone_number': '01212231815', 'role_group': 'Admin'}
            st.rerun()

        st.write("---")
        phone_input = st.text_input("رقم الهاتف", key="login_phone")
        password_input = st.text_input("كلمة السر", type="password", key="login_pass")
        
        if st.button("دخول عالي الأمان"):
            if phone_input.strip() == "" or password_input.strip() == "":
                st.warning("⚠️ يرجى إدخال رقم الهاتف وكلمة السر.")
            else:
                result = execute_query("SELECT user_id, full_name, phone_number, password_hash, role_group, account_status FROM users WHERE phone_number = ?", (phone_input.strip(),), fetch=True)
                if result and len(result[1]) > 0:
                    user_id, full_name, phone, stored_hash, role_group, account_status = result[1][0]
                    if check_hashes(password_input, stored_hash):
                        st.session_state['logged_in'] = True
                        st.session_state['user_info'] = {'user_id': user_id, 'full_name': full_name, 'phone_number': phone, 'role_group': role_group if role_group else 'Admin'}
                        st.success("✅ تم تسجيل الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("❌ كلمة السر غير صحيحة.")
                else:
                    st.error("❌ لا يوجد حساب مسجل برقم الهاتف هذا.")

    with tab_register:
        st.subheader("إنشاء حساب موظف جديد")
        reg_name = st.text_input("الاسم بالكامل", key="reg_name")
        reg_phone = st.text_input("رقم الهاتف", key="reg_phone")
        reg_pass = st.text_input("كلمة السر", type="password", key="reg_pass")
        reg_pass_confirm = st.text_input("تأكيد كلمة السر", type="password", key="reg_pass_confirm")
        
        if st.button("إنشاء الحساب"):
            if reg_name.strip() == "" or reg_phone.strip() == "" or reg_pass.strip() == "":
                st.warning("⚠️ يرجى ملء كافة البيانات.")
            elif reg_pass != reg_pass_confirm:
                st.error("❌ كلمة السر وتأكيدها غير متطابقين.")
            else:
                existing_user = execute_query("SELECT user_id FROM users WHERE phone_number = ?", (reg_phone.strip(),), fetch=True)
                if existing_user and len(existing_user[1]) > 0:
                    st.error("❌ رقم الهاتف مسجل بالفعل.")
                else:
                    hashed_password = make_hashes(reg_pass)
                    insert_sql = "INSERT INTO users (full_name, phone_number, password_hash, role_group, account_status) VALUES (?, ?, ?, 'Admin', 'Active')"
                    if execute_query(insert_sql, (reg_name.strip(), reg_phone.strip(), hashed_password)):
                        st.success("🎉 تم إنشاء الحساب وتفعيله بنجاح! اذهب لتبويب 'تسجيل الدخول' والدخول مباشرة.")