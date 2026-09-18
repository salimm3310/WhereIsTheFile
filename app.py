# ---------------------------------------------------------
    # التبويب 6: تقييم الأداء المطور بـ المعاينة، تصدير PDF، والصور الذكية AI
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
            
            # جلب شحنات وشركات الموظف
            emp_shipments = [s for s in st.session_state['active_shipments'] if s.get('last_status_updater') == u['full_name']]
            closed_ops = len([s for s in emp_shipments if s.get('status') == 'Closed'])
            total_ops = len(emp_shipments)
            emp_companies = list(set([s['company'] for s in emp_shipments if 'company' in s and s['company']]))
            
            # حساب النسبة المئوية الدقيقة
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
            
            # حالة المعاينة المباشرة قبل الحفظ
            if f'show_preview_{u_id}' not in st.session_state:
                st.session_state[f'show_preview_{u_id}'] = False

            # لوحة تعديل النقاط والملاحظات والصورة بالـ AI والرفع المباشر
            with st.expander(f"✏️ تعديل النقاط وملاحظات المدير وصورة الموظف لـ ({selected_card_emp})"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_earned = st.number_input("تعديل النقاط المكتسبة:", min_value=0, value=card_user_data['النقاط المكتسبة'], key=f"e_ear_{u_id}")
                    edit_deducted = st.number_input("تعديل الخصومات والتأخيرات:", min_value=0, value=card_user_data['الخصومات والتأخير'], key=f"e_ded_{u_id}")
                    edit_admin_notes = st.text_area("ملاحظات المدير الإدارية:", value=card_user_data['ملاحظات المدير'], height=80, key=f"e_not_{u_id}")

                with col_e2:
                    st.markdown("**🖼️ صورة الموظف (رفع مباشرة أو بالـ AI):**")
                    uploaded_img = st.file_uploader("1. رفع صورة مباشرة:", type=["jpg", "png", "jpeg"], key=f"up_img_{u_id}")
                    if uploaded_img:
                        st.session_state['user_photos'][u_id] = uploaded_img.getvalue()

                    st.markdown("---")
                    st.markdown("**2. مولد الصور الشخصية بالذكاء الاصطناعي (AI Headshot Generator 4K):**")
                    ai_prompt = st.text_input("وصف الصورة النصية المحدثة:", value=f"High quality formal professional headshot portrait of {selected_card_emp}, logistics business manager, neutral office background, 4k ultra realistic", key=f"ai_p_{u_id}")
                    
                    if st.button("✨ توليد وتوليد صورة عالية الجودة بالـ AI", key=f"btn_ai_{u_id}"):
                        st.session_state['user_photos'][u_id] = "AI_GENERATED"
                        st.success("✅ تم توليد وتحديث الصورة الاحترافية بالذكاء الاصطناعي!")

                col_btn_p1, col_btn_p2 = st.columns(2)
                with col_btn_p1:
                    if st.button("👁️ معاينة الكارت المحدث قبل الحفظ", key=f"btn_prev_{u_id}"):
                        st.session_state[f'show_preview_{u_id}'] = True
                        st.info("🔍 تم تفعيل وضع المعاينة المباشرة للكارت أدناه!")

                with col_btn_p2:
                    if st.button("💾 حفظ واعتماد التعديلات نهائياً", key=f"btn_save_eval_{u_id}"):
                        st.session_state['user_points'][u_id] = {
                            "earned": edit_earned,
                            "deducted": edit_deducted,
                            "notes": edit_admin_notes.strip()
                        }
                        st.session_state[f'show_preview_{u_id}'] = False
                        st.success("✅ تم حفظ واعتماد التعديلات بنجاح!")
                        st.rerun()

            st.write("---")

            # تصدير الكارت إلى ملف PDF صفحة واحدة
            pdf_html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 2px solid #8c6d58; border-radius: 10px;">
                <h1 style="color:#4e342e; text-align:center;">Mohamed Salem OPS App - Official ID Card</h1>
                <hr>
                <h2>📇 الموظف: {card_user_data['الموظف']} (ID: #{u_id})</h2>
                <p><strong>المجموعة:</strong> {card_user_data['المجموعة']}</p>
                <p><strong>صافي التقييم:</strong> {card_user_data['صافي التقييم']} نقطة ({card_user_data['التصنيف']} - {card_user_data['النسبة المئوية']})</p>
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
                if photo_data and photo_data != "AI_GENERATED":
                    st.image(photo_data, width=200, caption=card_user_data['الموظف'])
                elif photo_data == "AI_GENERATED":
                    st.markdown("<div style='width:200px; height:200px; background: linear-gradient(135deg, #4e342e, #8c6d58); color:white; display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:16px; font-size:20px; font-weight:bold; border:3px solid #8c6d58;'><span style='font-size:50px;'>🤖</span>AI Generated 4K</div>", unsafe_allow_html=True)
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