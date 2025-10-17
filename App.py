import streamlit as st
import pandas as pd
from io import StringIO
import re # สำหรับใช้ regular expression ในการแยก Code Mapping Skill

# ใช้ st.cache_data เพื่อโหลดข้อมูลเพียงครั้งเดียวและแคชไว้เพื่อประสิทธิภาพที่ดีขึ้น
@st.cache_data
def load_data(uploaded_file):
    """
    ฟังก์ชันสำหรับโหลดไฟล์ CSV ไปยัง Pandas DataFrame
    """
    if uploaded_file is not None:
        # อ่านไฟล์ CSV ที่อัปโหลด
        try:
            # ใช้ StringIO สำหรับการอ่านไฟล์ที่อัปโหลด
            dataframe = pd.read_csv(StringIO(uploaded_file.getvalue().decode("utf-8")))
            # แปลงคอลัมน์สำคัญให้เป็น string เพื่อให้การเปรียบเทียบทำงานได้ง่าย
            # ต้องมั่นใจว่าชื่อคอลัมน์ถูกต้องตามไฟล์ CSV ของคุณ
            if '[ID]' in dataframe.columns:
                dataframe['[ID]'] = dataframe['[ID]'].astype(str)
            if '[Code Mapping Skill]' in dataframe.columns:
                # ทำให้แน่ใจว่าค่าในคอลัมน์นี้เป็น string
                dataframe['[Code Mapping Skill]'] = dataframe['[Code Mapping Skill]'].astype(str)
            
            return dataframe
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์: {e}")
            return None
    return None

st.set_page_config(page_title="CSV Search Engine", layout="wide")

st.title("🔍 Search Engine จากไฟล์ CSV")

# ส่วนสำหรับอัปโหลดไฟล์
uploaded_file = st.file_uploader("Upload ไฟล์ CSV ของคุณ", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        st.success("โหลดไฟล์สำเร็จ!")
        st.subheader("ข้อมูลทั้งหมด (5 แถวแรก)")
        st.dataframe(df.head())
        
        # -----------------------------------------------------
        ## ฟอร์มค้นหา
        # -----------------------------------------------------
        st.subheader("ค้นหาข้อมูล")
        
        # ช่องรับ ID
        id_input = st.text_input("กรอก ID (เช่น '200027')")
        
        # ช่องรับ Code Mapping Skill (ใช้ st.multiselect เพื่อเลือกได้หลายค่า)
        # ดึงค่าที่เป็นไปได้ทั้งหมดจากคอลัมน์ Code Mapping Skill 
        # (ต้องจัดการกับรูปแบบข้อมูลในคอลัมน์นี้ถ้ามีหลายค่าในเซลล์เดียว)
        
        # สำหรับกรณีที่ค่าในคอลัมน์ [Code Mapping Skill] อาจมีหลายค่าคั่นด้วยคอมม่า
        unique_skills = set()
        if '[Code Mapping Skill]' in df.columns:
            for item in df['[Code Mapping Skill]'].dropna().unique():
                # สมมติว่าในเซลล์อาจมีค่าเป็น '1', '1,2', '3', 
                # เราจะแยกค่าแต่ละตัวออกมา
                for skill in re.split(r'[,;]\s*', str(item)): # แยกด้วยคอมม่าหรือเซมิโคลอน
                    if skill.strip():
                        unique_skills.add(skill.strip())
            
        skill_options = sorted(list(unique_skills))
        
        skill_input = st.multiselect(
            "เลือก Code Mapping Skill (เช่น '1', '2')",
            options=skill_options,
            default=[] # เริ่มต้นไม่มีการเลือกใดๆ
        )
        
        search_button = st.button("ค้นหา")
        
        # -----------------------------------------------------
        ## การประมวลผลการค้นหา
        # -----------------------------------------------------
        if search_button:
            if not id_input and not skill_input:
                st.warning("โปรดกรอก ID หรือเลือก Code Mapping Skill อย่างน้อยหนึ่งอย่างเพื่อค้นหา")
            else:
                filtered_df = df.copy()
                
                # เงื่อนไขที่ 1: [ID] = '200027'
                if id_input:
                    # ใช้ .str.contains เพื่อรองรับ ID ที่ไม่ตรงกันเป๊ะถ้าต้องการความยืดหยุ่น 
                    # แต่ถ้าต้องการตรงเป๊ะแบบ SQL ต้องใช้ == 
                    filtered_df = filtered_df[filtered_df['[ID]'] == id_input.strip()] 
                
                # เงื่อนไขที่ 2: [Code Mapping Skill] in ('1','2')
                if skill_input:
                    # สร้าง mask สำหรับการกรองทีละแถว
                    skill_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                    
                    # ตรวจสอบว่ามีค่าที่เลือกอยู่ในคอลัมน์ [Code Mapping Skill] หรือไม่
                    # แม้ว่าคอลัมน์นั้นจะมีหลายค่าคั่นด้วยคอมม่า (หรือตัวคั่นอื่นๆ)
                    if '[Code Mapping Skill]' in filtered_df.columns:
                        for skill in skill_input:
                            # ตรวจสอบว่า string ของ skill ที่เลือกนั้น
                            # เป็นส่วนหนึ่งของ string ในคอลัมน์ [Code Mapping Skill] หรือไม่ 
                            # โดยใช้ \b เพื่อให้แน่ใจว่าเป็นคำเต็ม (เช่น ไม่ใช่ค้นหา '1' แล้วได้ '10')
                            regex_pattern = r'\b' + re.escape(skill.strip()) + r'\b'
                            skill_mask = skill_mask | filtered_df['[Code Mapping Skill]'].str.contains(regex_pattern, na=False)

                    filtered_df = filtered_df[skill_mask]
                
                # เงื่อนไขที่ 3: Group By ID, OPCode
                # ใน Pandas การ Group By มักใช้สำหรับการสรุปข้อมูล (aggregation) 
                # แต่ถ้าคุณต้องการแค่แสดงผลลัพธ์ที่ไม่ซ้ำกัน (distinct combinations) 
                # ของ ID และ OPCode ที่ตรงตามเงื่อนไขการค้นหา คุณสามารถใช้ .drop_duplicates()
                
                # สมมติว่าคุณต้องการแค่แถวที่ไม่ซ้ำกันของผลลัพธ์การค้นหา
                if '[ID]' in filtered_df.columns and 'OPCode' in filtered_df.columns:
                    final_result_df = filtered_df.drop_duplicates(subset=['[ID]', 'OPCode'])
                else:
                    final_result_df = filtered_df
                
                # -----------------------------------------------------
                ## แสดงผลลัพธ์
                # -----------------------------------------------------
                st.subheader(f"ผลลัพธ์การค้นหา ({len(final_result_df)} แถว)")
                
                if final_result_df.empty:
                    st.info("ไม่พบข้อมูลที่ตรงกับเงื่อนไขการค้นหา")
                else:
                    st.dataframe(final_result_df, use_container_width=True)
                    
    elif df is not None and df.empty:
        st.error("ไฟล์ CSV ว่างเปล่าหรือไม่มีข้อมูลที่สามารถอ่านได้")

# เพิ่มวิธีใช้งาน (Optional)
st.markdown("---")
st.markdown("""
### 💡 คำแนะนำการใช้งาน:
1.  **เตรียมไฟล์:** ตรวจสอบให้แน่ใจว่าไฟล์ CSV ของคุณมีคอลัมน์ชื่อ `[ID]` และ `[Code Mapping Skill]`
2.  **อัปโหลด:** กดปุ่ม **Browse files** เพื่ออัปโหลดไฟล์ CSV
3.  **ค้นหา:** กรอกค่า **ID** และเลือก **Code Mapping Skill** ที่ต้องการ
4.  **ผลลัพธ์:** กดปุ่ม **ค้นหา** เพื่อดูผลลัพธ์ในตารางด้านล่าง
""")
