import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# ---------------------------------------------------------
# 1. تهيئة إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mohamed Salem OPS App",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. تهيئة البيانات الأساسية بالنظام (Session State)
# ---------------------------------------------------------
if 'registered_users' not in st.session_state:
    st.session_state['registered_users'] = [
        {"user_id": 1, "username": "admin", "password": "123", "full_name": "Mohamed Salem", "role_group": "Admin", "phone_number": "01212231815", "status": "Active"},
        {"user_id": 2, "username": "ops1", "password": "123", "full_name": "أحمد محمود", "role_group": "Operations", "phone_number": "01000000001", "status": "Active"},
        {"user_id": 3, "username": "sales1", "password": "123", "full_name": "سارة علي", "role_group": "Sales", "phone_number": "01000000002", "status": "Active"}
    ]

if 'active_shipments' not in st.session_state:
    st.session_state['active_shipments'] = [
        {"file_num": "260862115", "company": "U.S.C", "inv": "3A - 3B", "bkg": "BKG-992", "status": "Under Operation", "last_status_updater": "أحمد محمود"},
        {"file_num": "260962779", "company": "Global Trade", "inv": "908013", "bkg": "BKG-104", "status": "Closed", "last_status_updater": "Mohamed Salem"}
    ]

if 'internal_messages' not in st.session_state:
    st.session_state['internal_messages'] = []

if 'whatsapp_logs' not in st.session_state:
    st.session_state['whatsapp_logs'] = []

if 'user_points' not in st.session_state:
    st.session_state['user_points'] = {
        1: {"earned": 2, "deducted": 0, "notes": "إغلاق ملفات مكتملة"},
        2: {"earned": 1, "deducted": 1, "notes": "إغلاق ملف وتأخير سابق"},
        3: {"earned": 0, "deducted": 0, "notes": ""}
    }

if 'user_photos' not in st.session_state:
    st.session_state['user_photos'] = {}

if 'logged_user' not in st.session_state:
    st.session_state['logged_user'] = st.session_state['registered_users'][0]

user = st.session_state['logged_user']

# ---------------------------------------------------------
# 3. دالة تنسيق رقم الواتساب
# ---------------------------------------------------------
def format_whatsapp_phone(phone_str):
    clean = ''.join(filter(str.isdigit, str(phone_str)))
    if clean.startswith("0"):
        clean = "20" + clean[1:]
    elif not clean.startswith("20"):
        clean = "2" + clean
    return clean

# ---------------------------------------------------------
# 4. القائمة الجانبية الهيكلية
# ---------------------------------------------------------
st.sidebar.title(f"👤 {user['full_name']}")
st.sidebar.caption(f"المجموعة: {user['role_group']}")

menu_options = [
    "⚙️ لوحة التحكم الإدارية (Admin Panel)",
    "📊 لوحة التحليلات الأداء (Analytics Dashboard)",
    "⏳ تتبع دوره حياة الملفات والتأخيرات (SLA)",
    "📦 إضافة إدارة وتحديث حالة شحنة (11 حقل)",
    "💬 المراسلات والواتساب (Messaging & WhatsApp)",
    "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)",
    "📜 سجل الحالات والتدقيق (Status Logs & Audit Trail)"
]

choice = st.sidebar.radio("الانتقال إلى الشاشة:", menu_options)

# ---------------------------------------------------------
# التبويب 1: لوحة التحكم الإدارية (Admin Panel)
# ---------------------------------------------------------
if choice == "⚙️ لوحة التحكم الإدارية (Admin Panel)":
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
# التبويب 2: لوحة التحليلات
# ---------------------------------------------------------
elif choice == "📊 لوحة التحليلات الأداء (Analytics Dashboard)":
    st.subheader("📊 لوحة التحليلات الأداء (Analytics Dashboard)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("إجمالي الشحنات", len(st.session_state['active_shipments']))
    with col2:
        st.metric("الشحنات قيد التشغيل", len([s for s in st.session_state['active_shipments'] if s['status'] != 'Closed']))
    with col3:
        st.metric("الملفات المغلقة", len([s for s in st.session_state['active_shipments'] if s['status'] == 'Closed']))

    st.markdown("### 📋 تفاصيل الشحنات والمؤشرات")
    st.dataframe(pd.DataFrame(st.session_state['active_shipments']), use_container_width=True)

# ---------------------------------------------------------
# التبويب 3: SLA
# ---------------------------------------------------------
elif choice == "⏳ تتبع دوره حياة الملفات والتأخيرات (SLA)":
    st.subheader("⏳ تتبع دوره حياة الملفات والتأخيرات (SLA)")
    st.info("💡 متابعة دورة SLA والتأخيرات التشغيلية.")
    st.dataframe(pd.DataFrame(st.session_state['active_shipments']), use_container_width=True)

# ---------------------------------------------------------
# التبويب 4: شاشة الشحنات 11 حقل
# ---------------------------------------------------------
elif choice == "📦 إضافة إدارة وتحديث حالة شحنة (11 حقل)":
    st.subheader("📦 إضافة إدارة وتحديث حالة شحنة (11 حقل)")
    st.dataframe(pd.DataFrame(st.session_state['active_shipments']), use_container_width=True)

# ---------------------------------------------------------
# التبويب 5: المراسلات والواتساب
# ---------------------------------------------------------
elif choice == "💬 المراسلات والواتساب (Messaging & WhatsApp)":
    st.subheader("المراسالات")
    tab_msg, tab_wa = st.tabs(["📩 الرسائل الداخلية النظامية", "WhatsApp"])

    with tab_msg:
        col_send, col_inbox = st.columns([2, 3])
        with col_send:
            st.markdown("### 📤 إرسال رسالة داخلية")
            active_users_list = [u for u in st.session_state['registered_users'] if u['status'] == 'Active']
            emp_map = {f"{u['full_name']} ({u['role_group']})": u for u in active_users_list}
            target_emp_label = st.selectbox("إلى المستخدم / الفريق:", list(emp_map.keys()))
            target_emp_obj = emp_map[target_emp_label]

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
                user_editable_text = st.text_area("نص التحديث التوضيحي:", value=dynamic_body, height=160)
            else:
                user_editable_text = st.text_area("نص الرسالة الداخلية:", height=120)

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
                    st.success("✅ تم إرسال الرسالة الداخلية بنجاح!")
                    st.rerun()

        with col_inbox:
            st.markdown("### 📥 صندوق الرسائل الواردة")
            for msg in reversed(st.session_state['internal_messages']):
                st.markdown(f"**من: {msg.get('sender')} ➔ إلى: {msg.get('recipient')}** ({msg.get('time')})\n\n{msg.get('text')}\n---")

    with tab_wa:
        st.markdown("### WhatsApp")
        recipient_type = st.radio("تحديد نوع المستلم:", ["مستخدم/موظف بالبرنامج", "العميل"], horizontal=True)

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
                st.info(f"📱 رقم الهاتف المسجل: **{target_phone}**")
            header_greeting = f"مرحباً أستاذ/ة {target_name}"

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
# التبويب 6: تقييم الأداء والمكافآت
# ---------------------------------------------------------
elif choice == "📊 تقارير تقييم الأداء والمكافآت (Performance & Bonus)":
    st.subheader("تقييم الاداء")
    st.success("✅ قاعدة التقييم المعتمدة بالنظام: 1 نقطة لكل ملف مكتمل ومغلق (Closed).")

    st.markdown("#### 🎛️ لوحة التحكم لتشكيل وفلترة تقارير الأداء")
    c_f1, c_f2 = st.columns(2)

    active_users_eval = [u for u in st.session_state['registered_users'] if u['status'] == "Active"]
    emp_names_list = ["الكل"] + [u['full_name'] for u in active_users_eval]

    with c_f1:
        filter_emp = st.selectbox("👤 تحديد الموظف:", emp_names_list)
    with c_f2:
        filter_rank = st.selectbox("🏆 ترتيب الأداء والتقييم:", ["الكل (افتراضي)", "الأعلى تقييماً (Top Performers)", "الأقل تقييماً (Lowest Performers)"])

    raw_eval_list = []
    for u in active_users_eval:
        pts = st.session_state['user_points'].get(u['user_id'], {"earned": 0, "deducted": 0, "notes": ""})
        net = pts['earned'] - pts['deducted']
        
        emp_shipments = [s for s in st.session_state['active_shipments'] if s.get('last_status_updater') == u['full_name']]
        closed_ops = len([s for s in emp_shipments if s.get('status') == 'Closed'])
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

    st.write("---")
    st.markdown("### 💳 كارت الموظف المزدوج (Canva Modern Business ID Card)")
    selected_card_emp = st.selectbox("اختر الموظف", [u['full_name'] for u in active_users_eval])
    card_user_data = next((item for item in raw_eval_list if item['الموظف'] == selected_card_emp), None)

    if card_user_data:
        u_id = card_user_data['user_id']

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

            if st.button("💾 حفظ واعتماد التعديلات نهائياً", key=f"btn_save_eval_{u_id}"):
                st.session_state['user_points'][u_id] = {
                    "earned": edit_earned,
                    "deducted": edit_deducted,
                    "notes": edit_admin_notes.strip()
                }
                st.success("✅ تم حفظ التعديلات بنجاح!")
                st.rerun()

        st.write("---")
        st.markdown("#### 📄 الوجه الأول: البيانات الشخصية والصورة")
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
# التبويب 7: سجل الحالات والتدقيق
# ---------------------------------------------------------
elif choice == "📜 سجل الحالات والتدقيق (Status Logs & Audit Trail)":
    st.subheader("📜 سجل الحالات والتدقيق (Status Logs & Audit Trail)")
    st.markdown("### 🔍 تتبع كافة عمليات التحديث والتدقيق بالنظام")
    st.info("💡 يتم أرشفة وتوثيق كافة رسائل وتحديثات الشحنات والحالات التشغيلية تلقائياً.")