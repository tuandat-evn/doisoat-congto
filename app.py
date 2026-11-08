import streamlit as st
from core_elster import xu_ly_file_elster
from core_gelex import xu_ly_file_gelex
from core_dts27_xanh import xu_ly_file_dts27_xanh
from core_dts27_do import xu_ly_file_dts27_do
from core_psmart import xu_ly_file_psmart
from core_hhm import xu_ly_file_hhm
from core_vinasino import xu_ly_file_vinasino
import io
import os
import pandas as pd
from docx import Document
import zipfile
import pdfplumber
st.set_page_config(page_title="Tool Đối Soát Công Tơ", page_icon="⚡", layout="wide")

st.markdown("""
    <div style='position: relative; text-align: center; padding: 20px; background-color: #f0f8ff; border-radius: 10px; margin-bottom: 25px;'>
        <h1 style='color: #005A9C; margin-bottom: 0px;'>⚡ HỆ THỐNG ĐỐI SOÁT LẬP TRÌNH CÔNG TƠ ĐIỆN TỬ</h1>
        <p style='color: #FF6600; font-size: 18px; font-weight: bold; margin-top: 5px;'>Tự động hóa - Chính xác - Tối ưu thời gian</p>
        <div style='position: absolute; bottom: 10px; right: 20px; text-align: right;'>
            <div style='font-size: 22px; font-weight: bold; color: #004b87; letter-spacing: 0.5px; font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;'>PC THƯỜNG TÍN</div>
            <div style='font-size: 12px; font-style: italic; color: #666666; margin-top: 2px;'>Directed by AE HN11</div>
        </div>
    </div>
""", unsafe_allow_html=True)

loai_cong_to = st.selectbox(
    "📍 Chọn loại công tơ (Hoặc để mặc định):",
    [
        "[ ⚡ Tự động nhận diện thông minh ]", 
        "Công tơ ELSTER A1700", 
        "Công tơ GELEX ME",
        "Công tơ DTS27 ĐỎ",
        "Công tơ DTS27 XANH",
        "Công tơ PSMART",
        "Công tơ HHM",
        "Công tơ VINASINO"
    ]
)
st.markdown("---")

# --- CHỨC NĂNG XÓA FILE KHOA HỌC (RESET APP) ---
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

col_upload, col_reset = st.columns([8, 2])

with col_upload:
    uploaded_files = st.file_uploader(
        "📥 Kéo thả các file PDF (Trước/Sau cài đặt) vào đây", 
        type=['pdf'], 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['uploader_key']}"
    )
    uploaded_excel = st.file_uploader(
            "📊 Tải lên Excel danh sách Khách hàng (Tùy chọn điền Biên bản)", 
            type=["xlsx", "xls"]
        )

with col_reset:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Xóa toàn bộ file", use_container_width=True, type="secondary"):
        st.session_state["uploader_key"] += 1
        st.rerun()

def tao_chuoi_gio(danh_sach_gio, is_dat):
    if not danh_sach_gio: return "-"
    css_class = "tag-green" if is_dat else "tag-red"
    icon = "v" if is_dat else "x"
    return "<br>".join([f'<span class="{css_class}">{gio} {icon}</span>' for gio in danh_sach_gio])

# HÀM XỬ LÝ XUẤT FILE WORD / ZIP BIÊN BẢN
def thuc_hien_xuat_word_hang_loat(ban_ghi_hoan_thien):
    file_mau = "Mau_Bien_Ban.docx"
    if not os.path.exists(file_mau): return None, False
        
    danh_sach_serial = set([item["serial"] for item in ban_ghi_hoan_thien if item["serial"] != "N/A"])
    kho_file_word = {}
    
    for s in danh_sach_serial:
        cac_file_cung_serial = [item for item in ban_ghi_hoan_thien if item["serial"] == s]
        d_truoc = next((item for item in cac_file_cung_serial if item["giai_doan"] == "TRƯỚC"), None)
        d_sau = next((item for item in cac_file_cung_serial if item["giai_doan"] == "SAU"), None)
        
        if d_truoc and d_sau:
            doc = Document(file_mau)
            replacements = {
                "{{serial}}": str(d_truoc["serial"]), "{{tu_ti}}": f"{d_truoc['tu']}/{d_truoc['ti']}",
                "{{sl_tr}}": str(d_truoc["lan_cai_dat"]), "{{ngay_tr}}": str(d_truoc["ngay_lap_trinh"]),
                "{{p_giao_tr}}": f"{d_truoc['p_giao']:,}", "{{b1_giao_tr}}": f"{d_truoc['b1_giao']:,}",
                "{{b2_giao_tr}}": f"{d_truoc['b2_giao']:,}", "{{b3_giao_tr}}": f"{d_truoc['b3_giao']:,}",
                "{{p_nhan_tr}}": f"{d_truoc['p_nhan']:,}", "{{b1_nhan_tr}}": f"{d_truoc['b1_nhan']:,}",
                "{{b2_nhan_tr}}": f"{d_truoc['b2_nhan']:,}", "{{b3_nhan_tr}}": f"{d_truoc['b3_nhan']:,}",
                "{{q_giao_tr}}": f"{d_truoc['q_giao']:,}", "{{q_nhan_tr}}": f"{d_truoc['q_nhan']:,}",
                "{{sl_sa}}": str(d_sau["lan_cai_dat"]), "{{ngay_sa}}": str(d_sau["ngay_lap_trinh"]),
                "{{p_giao_sa}}": f"{d_sau['p_giao']:,}", "{{b1_giao_sa}}": f"{d_sau['b1_giao']:,}",
                "{{b2_giao_sa}}": f"{d_sau['b2_giao']:,}", "{{b3_giao_sa}}": f"{d_sau['b3_giao']:,}",
                "{{p_nhan_sa}}": f"{d_sau['p_nhan']:,}", "{{b1_nhan_sa}}": f"{d_sau['b1_nhan']:,}",
                "{{b2_nhan_sa}}": f"{d_sau['b2_nhan']:,}", "{{b3_nhan_sa}}": f"{d_sau['b3_nhan']:,}",
                "{{q_giao_sa}}": f"{d_sau['q_giao']:,}", "{{q_nhan_sa}}": f"{d_sau['q_nhan']:,}",
                "{{TEN_KH}}": str(d_truoc.get('TEN_KH', '..............................')),
                "{{DIA_CHI}}": str(d_truoc.get('DIA_CHI', '..............................')),
                "{{NUOC_SX}}": str(d_truoc.get('NUOC_SX', '.......')),
                "{{K}}": str(d_truoc.get('K', '.......')),
                "{{LOAI_CT}}": str(d_truoc.get('LOAI_CT', '.......')),
                "{{CAP_CX}}": str(d_truoc.get('CAP_CX', '.......')),
                "{{HE_SO}}": str(d_truoc.get('HE_SO', '.......')),
                "{{TEN_CNQL}}": str(d_truoc.get('TEN_CNQL', '.........................'))
            }
            for p in doc.paragraphs:
                for k, v in replacements.items():
                    if k in p.text: p.text = p.text.replace(k, v)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            for k, v in replacements.items():
                                if k in p.text: p.text = p.text.replace(k, v)
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            kho_file_word[s] = bio.getvalue()

    if not kho_file_word: return None, False
    if len(kho_file_word) == 1:
        serial_du_nhat = list(kho_file_word.keys())[0]
        return io.BytesIO(kho_file_word[serial_du_nhat]), False
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for s, b_data in kho_file_word.items():
                zip_file.writestr(f"Bien_Ban_Cong_To_{s}.docx", b_data)
        zip_buffer.seek(0)
        return zip_buffer, True

# HÀM XỬ LÝ XUẤT FILE EXCEL TỔNG HỢP
def thuc_hien_xuat_excel(ban_ghi_hoan_thien):
    data_list = []
    for idx, d in enumerate(ban_ghi_hoan_thien):
        data_list.append({
            "STT": idx + 1, 
            "Giai đoạn": d["giai_doan"], 
            "Tên file PDF": d["file_name"], 
            "Số Serial": d["serial"], 
            "Loại công tơ": d["ten_cong_to"],
            "Số lần cài đặt": d["lan_cai_dat"], 
            "Ngày lập trình": d["ngay_lap_trinh"], 
            "Hệ số TU/TI": f"{d['tu']}/{d['ti']}",
            "Tổng P Giao (kWh)": d["p_giao"], 
            "B1 Giao (kWh)": d["b1_giao"], 
            "B2 Giao (kWh)": d["b2_giao"], 
            "B3 Giao (kWh)": d["b3_giao"],
            "Tổng P Nhận (kWh)": d["p_nhan"], 
            "B1 Nhận (kWh)": d["b1_nhan"], 
            "B2 Nhận (kWh)": d["b2_nhan"], 
            "B3 Nhận (kWh)": d["b3_nhan"],
            "Q Giao (kVArh)": d["q_giao"], 
            "Q Nhận (kVArh)": d["q_nhan"], 
            "Kết quả đối soát": d["text_ket_qua"].replace("● ", "")
        })
    df = pd.DataFrame(data_list)
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Báo cáo tổng hợp")
    bio.seek(0)
    return bio

if uploaded_files:
    st.info(f"⏳ Đang xử lý {len(uploaded_files)} file...")
    
    danh_sach_tho = []
    for file in uploaded_files:
        file.seek(0) # Đảm bảo file bắt đầu đọc từ trang đầu tiên
        
        # --- KỊCH BẢN 1: TỰ ĐỘNG NHẬN DIỆN THÔNG MINH ---
        if loai_cong_to == "[ ⚡ Tự động nhận diện thông minh ]":
            with pdfplumber.open(file) as pdf:
                text_preview = pdf.pages[0].extract_text() or ""
            
            file.seek(0) # RẤT QUAN TRỌNG: Trả file về vị trí ban đầu
            text_preview_lower = text_preview.lower()
            
            # Quét vân tay phân loại
            if "tên công tơ" in text_preview_lower or "số sx:" in text_preview_lower:
                data = xu_ly_file_gelex(file)
            elif "thông tin công tơ" in text_preview_lower:
                data = xu_ly_file_dts27_do(file)
            elif "program counter" in text_preview_lower or "ct value" in text_preview_lower:
                data = xu_ly_file_psmart(file)
            elif "hhm" in text_preview_lower:
                data = xu_ly_file_hhm(file)
            elif "vse" in text_preview_lower or "nbg" in text_preview_lower:
                data = xu_ly_file_vinasino(file)
            elif "meter number:" in text_preview_lower or "configuration program" in text_preview_lower:
                data = xu_ly_file_dts27_xanh(file)
            else:
                data = xu_ly_file_elster(file)
                
        # --- KỊCH BẢN 2: ÉP CHỌN BẰNG TAY GELEX ---
        elif loai_cong_to == "Công tơ GELEX ME":
            data = xu_ly_file_gelex(file)
            
        # --- KỊCH BẢN 3: ÉP CHỌN BẰNG TAY ELSTER ---
        elif loai_cong_to == "Công tơ ELSTER A1700":
            data = xu_ly_file_elster(file)
            
        # --- KỊCH BẢN 4: ÉP CHỌN BẰNG TAY DTS27 ĐỎ ---
        elif loai_cong_to == "Công tơ DTS27 ĐỎ":
            data = xu_ly_file_dts27_do(file)
            
        # --- KỊCH BẢN 5: ÉP CHỌN BẰNG TAY DTS27 XANH ---
        elif loai_cong_to == "Công tơ DTS27 XANH":
            data = xu_ly_file_dts27_xanh(file)

        # --- KỊCH BẢN 6: ÉP CHỌN BẰNG TAY PSMART ---
        elif loai_cong_to == "Công tơ PSMART":
            data = xu_ly_file_psmart(file)

        # --- KỊCH BẢN 7: ÉP CHỌN BẰNG TAY HHM ---
        elif loai_cong_to == "Công tơ HHM":
            data = xu_ly_file_hhm(file)
            # --- KỊCH BẢN 8: ÉP CHỌN BẰNG TAY VINASINO ---
        elif loai_cong_to == "Công tơ VINASINO":
            data = xu_ly_file_vinasino(file)
            
        # ----------------------------------------------------
        # BỘ LỌC CHỈ LẤY PHẦN NGUYÊN (GỌT SỐ THẬP PHÂN) CHO MỌI CÔNG TƠ
        cac_cot_chi_so = ["p_giao", "b1_giao", "b2_giao", "b3_giao", "p_nhan", "b1_nhan", "b2_nhan", "b3_nhan", "q_giao", "q_nhan"]
        for cot in cac_cot_chi_so:
            try:
                data[cot] = int(data[cot])
            except:
                pass # Lỡ có cột nào rỗng thì bỏ qua không báo lỗi
                
        data['file_name'] = file.name
        danh_sach_tho.append(data)
        
    ban_ghi_hoan_thien = []
    serials = set([d['serial'] for d in danh_sach_tho])
    
    for s in serials:
        cac_file_cung_serial = [d for d in danh_sach_tho if d['serial'] == s]
        cac_file_cung_serial.sort(key=lambda x: x['lan_cai_dat'])
        
        for i, file_data in enumerate(cac_file_cung_serial):
            if len(cac_file_cung_serial) == 1:
                if file_data['is_tt60']:
                    file_data['giai_doan'] = "SAU"
                    file_data['text_ket_qua'] = "● ĐẠT (TT60)"
                    file_data['is_hop_le'] = True
                elif file_data['is_tt16']:
                    file_data['giai_doan'] = "TRƯỚC"
                    file_data['text_ket_qua'] = "● ĐẠT (TT16)"
                    file_data['is_hop_le'] = True
                else:
                    file_data['giai_doan'] = "CHƯA RÕ"
                    file_data['text_ket_qua'] = "● SAI GIỜ"
                    file_data['is_hop_le'] = False
            else:
                if i == 0:
                    file_data['giai_doan'] = "TRƯỚC"
                    if file_data['is_tt16']:
                        file_data['text_ket_qua'] = "● ĐẠT (TT16)"
                        file_data['is_hop_le'] = True
                    else:
                        file_data['text_ket_qua'] = "❌ SAI BIỂU GIÁ CŨ"
                        file_data['is_hop_le'] = False
                else:
                    file_data['giai_doan'] = "SAU"
                    if file_data['is_tt60']:
                        file_data['text_ket_qua'] = "● ĐẠT (TT60)"
                        file_data['is_hop_le'] = True
                    else:
                        file_data['text_ket_qua'] = "❌ LỖI: VẪN GIỮ GIỜ CŨ"
                        file_data['is_hop_le'] = False
            ban_ghi_hoan_thien.append(file_data)

    # --- KHU VỰC VẼ BẢNG HTML VŨ TRỤ ---
    html_table = """
    <style>
        .custom-table {width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; margin-bottom: 5px; white-space: nowrap;}
        .custom-table th {background-color: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; text-align: center; color: #1e3a8a; font-weight: 600;}
        .custom-table td {padding: 8px 12px; border: 1px solid #dee2e6; text-align: center; vertical-align: middle;}
        .tag-green {background-color: #e6f4ea; color: #1e8e3e; padding: 3px 6px; border-radius: 8px; display: inline-block; margin: 2px 0; font-size: 11px; border: 1px solid #ceead6;}
        .tag-red {background-color: #fce8e6; color: #d93025; padding: 3px 6px; border-radius: 8px; display: inline-block; margin: 2px 0; font-size: 11px; border: 1px solid #fad2cf;}
        .badge-green {background-color: #1e8e3e; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;}
        .badge-red {background-color: #d93025; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;}
        .col-so {font-weight: bold; color: #0d47a1;}
    </style>
    <div style="overflow-x: auto; padding-bottom: 5px;">
    <table class="custom-table">
        <thead>
            <tr>
                <th rowspan="2">#</th><th rowspan="2">GIAI ĐOẠN</th><th rowspan="2">TÊN FILE</th><th rowspan="2">SERIAL</th><th rowspan="2">LOẠI CÔNG TƠ</th>
                <th colspan="3">THÔNG TIN LẬP TRÌNH</th><th colspan="4">P GIAO (kWh)</th><th colspan="4">P NHẬN (kWh)</th>
                <th colspan="2">VÔ CÔNG (kVArh)</th><th colspan="3">THỨ 2 -> THỨ 7</th><th colspan="2">CHỦ NHẬT</th><th rowspan="2">KẾT QUẢ ĐỐI SOÁT</th>
            </tr>
            <tr>
                <th>SL LP</th><th>NGÀY GẦN NHẤT</th><th>TU/TI</th>
                <th>TỔNG</th><th>B1</th><th>B2</th><th>B3</th>
                <th>TỔNG</th><th>B1</th><th>B2</th><th>B3</th>
                <th>Q GIAO</th><th>Q NHẬN</th>
                <th>T3</th><th>T1</th><th>T2</th><th>T3</th><th>T1</th>
            </tr>
        </thead>
        <tbody>
    """
    all_dat = True
    for idx, d in enumerate(ban_ghi_hoan_thien):
        if not d['is_hop_le']: all_dat = False
        badge_style = "badge-green" if d['is_hop_le'] else "badge-red"
        is_gio_dung = d['is_tt60'] if d['giai_doan'] == "SAU" else d['is_tt16']
        row_html = f"<tr><td>{idx+1}</td>{'<td style="background-color: #fee2e2; color: #dc2626; font-weight: bold;">SAU</td>' if d['giai_doan'] == 'SAU' else '<td><b>TRƯỚC</b></td>'}<td style='color: #1976d2; text-align: left;'>{d['file_name']}</td><td>{d['serial']}</td><td><b>{d.get('ten_cong_to', 'N/A')}</b></td><td>{d['lan_cai_dat']}</td><td>{d['ngay_lap_trinh']}</td><td>{d['tu']}/{d['ti']}</td><td class='col-so'>{d['p_giao']:,}</td><td class='col-so'>{d['b1_giao']:,}</td><td class='col-so'>{d['b2_giao']:,}</td><td class='col-so'>{d['b3_giao']:,}</td><td class='col-so' style='color: #d84315;'>{d['p_nhan']:,}</td><td class='col-so' style='color: #d84315;'>{d['b1_nhan']:,}</td><td class='col-so' style='color: #d84315;'>{d['b2_nhan']:,}</td><td class='col-so' style='color: #d84315;'>{d['b3_nhan']:,}</td><td class='col-so'>{d['q_giao']:,}</td><td class='col-so'>{d['q_nhan']:,}</td><td>{tao_chuoi_gio(d['thuc_te_nt']['T3'], is_gio_dung)}</td><td>{tao_chuoi_gio(d['thuc_te_nt']['T1'], is_gio_dung)}</td><td>{tao_chuoi_gio(d['thuc_te_nt']['T2'], is_gio_dung)}</td><td>{tao_chuoi_gio(d['thuc_te_cn']['T3'], is_gio_dung)}</td><td>{tao_chuoi_gio(d['thuc_te_cn']['T1'], is_gio_dung)}</td><td><span class='{badge_style}'>{d['text_ket_qua']}</span></td></tr>"
        html_table += row_html
        # Đổi màu ô SAU sau khi đã ráp xong chuỗi html
        if d['giai_doan'] == "SAU":
            row_html = row_html.replace("<td><b>SAU</b></td>", "<td style='background-color: #fee2e2; color: #dc2626; font-weight: 900; font-size: 15px;'>SAU</td>")
    
    # CHÈN CHỮ KÝ BẢN QUYỀN MỜ XÁM VÀO GÓC PHẢI DƯỚI BẢNG
    html_table += """
        </tbody>
    </table>    
    </div>
    """
    st.markdown(html_table, unsafe_allow_html=True)
    
    if all_dat: st.success("✅ Tuyệt vời! Các file đều đạt chuẩn cấu hình khung giờ.")
    else: st.error("⚠️ Cảnh báo: Phát hiện cấu hình có sai lệch hoặc lỗi lập trình biểu giá!")
# =====================================================================
# --- HỆ THỐNG RADAR CẢNH BÁO THÔNG MINH (QC CHECK) GIAO DIỆN MỚI ---
# =====================================================================
if 'ban_ghi_hoan_thien' in locals() and len(ban_ghi_hoan_thien) > 0:
    danh_sach_canh_bao = [] # Tạo một cái "giỏ" để gom tất cả lỗi lại
    danh_sach_serial_check = set([item["serial"] for item in ban_ghi_hoan_thien if item.get("serial") and item["serial"] != "N/A"])
    
    for s in danh_sach_serial_check:
        cac_file = [item for item in ban_ghi_hoan_thien if item.get("serial") == s]
        d_tr = next((item for item in cac_file if item.get("giai_doan") == "TRƯỚC"), None)
        d_sa = next((item for item in cac_file if item.get("giai_doan") == "SAU"), None)
        
        # 1. CẢNH BÁO SỐ LẦN LẬP TRÌNH NHẢY VỌT (Vượt quá +1)
        if d_tr and d_sa:
            try:
                lan_tr = int(d_tr.get("lan_cai_dat", 0))
                lan_sa = int(d_sa.get("lan_cai_dat", 0))
                if lan_sa > lan_tr + 1:
                    danh_sach_canh_bao.append(f"🔍 **Công tơ {s}:** Số lần lập trình tăng bất thường (Trước: {lan_tr} ➡️ Sau: {lan_sa}).")
            except:
                pass
        
        # 2. CẢNH BÁO CHỈ SỐ CÔNG TƠ ĐỀU BẰNG 0
        for d in [d_tr, d_sa]:
            if d:
                try:
                    # Cộng tổng tất cả 10 loại chỉ số xem có bằng 0 không
                    cac_chi_so = [float(d.get(k, 0)) for k in ['p_giao', 'b1_giao', 'b2_giao', 'b3_giao', 'p_nhan', 'b1_nhan', 'b2_nhan', 'b3_nhan', 'q_giao', 'q_nhan']]
                    if sum(cac_chi_so) == 0:
                        danh_sach_canh_bao.append(f"⚠️ **Công tơ {s} (Giai đoạn {d['giai_doan']}):** Toàn bộ chỉ số đang bằng 0. Anh em lưu ý rà soát lại!")
                except:
                    pass
                    
    # HÀNH ĐỘNG: Gói tất cả vào Hộp xổ xuống (Expander) để tiết kiệm diện tích
    if len(danh_sach_canh_bao) > 0:
        with st.expander(f"🚨 TỔNG HỢP QC: Phát hiện {len(danh_sach_canh_bao)} điểm bất thường cần rà soát (Bấm vào đây để xem chi tiết)"):
            for loi in danh_sach_canh_bao:
                st.warning(loi)
# =====================================================================
    # --- KHU VỰC PHÂN LUỒNG NÚT BẤM XUẤT FILE ĐA NĂNG ---
    # --- ĐỘNG CƠ VLOOKUP: GHÉP DỮ LIỆU EXCEL VÀO LIST KẾT QUẢ ---
if uploaded_excel is not None and 'ban_ghi_hoan_thien' in locals() and len(ban_ghi_hoan_thien) > 0:
    try:
        # Đọc file excel
        df_excel = pd.read_excel(uploaded_excel)
        
        # Chuẩn hóa cột SERIAL: Xóa khoảng trắng và tự động bù số 0 ở đầu cho đủ 12 ký tự
        df_excel['SERIAL'] = df_excel['SERIAL'].astype(str).str.strip().str.zfill(12)
        
        # Biến Excel thành từ điển để tra cứu siêu tốc
        dict_excel = df_excel.set_index('SERIAL').to_dict('index')
        
        # Chạy vòng lặp dò tìm Serial trong PDF để bơm thông tin Excel vào
        for d in ban_ghi_hoan_thien:
            # Chuẩn hóa Serial từ PDF cũng bù đủ số 0 để khớp lệnh tuyệt đối
            serial_pdf = str(d.get('serial', '')).strip().zfill(12)
            
            if serial_pdf in dict_excel:
                # Thấy mã khớp -> Đổ toàn bộ dữ liệu Khách hàng vào record này
                d.update(dict_excel[serial_pdf])
    except Exception as e:
        st.error(f"⚠️ Lỗi khi đọc file Excel Danh sách: {e}")
    # ==========================================
# --- KHU VỰC XUẤT FILE BIÊN BẢN & EXCEL ---
# ==========================================
if 'ban_ghi_hoan_thien' in locals() and len(ban_ghi_hoan_thien) > 0:
    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 3, 4])
    
    with col1:
        file_output, is_zip = thuc_hien_xuat_word_hang_loat(ban_ghi_hoan_thien)
        if file_output:
            if is_zip:
                st.download_button(label="📦 Xuất ZIP Toàn Bộ Biên Bản", data=file_output, file_name="Tron_Bo_Bien_Ban_Doi_Soat.zip", mime="application/zip", use_container_width=True)
            else:
                serial_single = ban_ghi_hoan_thien[0].get('serial', 'Unknown')
                st.download_button(label="📄 Xuất Word Biên Bản", data=file_output, file_name=f"Bien_Ban_Doi_Soat_{serial_single}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        else:
            st.button("📄 Xuất Word Biên Bản (Lỗi tạo file)", disabled=True, use_container_width=True)

    with col2:
        try:
            excel_data = thuc_hien_xuat_excel(ban_ghi_hoan_thien)
            if excel_data:
                st.download_button(
                    label="📊 Xuất Excel Tổng Hợp",
                    data=excel_data,
                    file_name="Bao_Cao_Tong_Hop_Doi_Soat.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Lỗi tạo Excel: {e}")