import pdfplumber
import re
from datetime import datetime

# 1. HÀM LÀM SẠCH SỐ LIỆU
def xu_ly_chi_so_gelex(chuoi_so):
    try:
        if not chuoi_so: return 0
        so_sach = str(chuoi_so).replace("kWh", "").replace("kvarh", "").replace(",", "").strip()
        return float(so_sach)
    except ValueError:
        return 0

# 2. HÀM QUÉT MÃ OBIS
def lay_chi_so_theo_obis(text, obis_pattern):
    pattern = obis_pattern + r'.*?([\d\.,]+)\s*(?:kWh|kvarh)'
    match = re.search(pattern, text, re.IGNORECASE)
    return xu_ly_chi_so_gelex(match.group(1)) if match else 0

# 3. HÀM DỊCH THUẬT KHUNG GIỜ
def phan_tich_khung_gio_gelex(text_day):
    moc_gio = re.findall(r'(\d{2}:\d{2})\s*(T[1-3])', text_day)
    if not moc_gio: return {'T1': [], 'T2': [], 'T3': []}

    ket_qua = {'T1': [], 'T2': [], 'T3': []}
    for i in range(len(moc_gio)):
        start_time = moc_gio[i][0]
        loai_bieu = moc_gio[i][1]
        end_time = moc_gio[i+1][0] if i < len(moc_gio) - 1 else "24:00"
        ket_qua[loai_bieu].append(f"{start_time}-{end_time}")
    return ket_qua

# 4. TRÁI TIM ĐỌC GELEX
def xu_ly_file_gelex(file_path):
    data = {}
    with pdfplumber.open(file_path) as pdf:
        text_all = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # --- THÔNG TIN CƠ BẢN ---
    match_so = re.search(r'Số SX:\s*(\d+)', text_all)
    data["serial"] = match_so.group(1) if match_so else "N/A"

    # ĐÃ THÊM: BÓC TÁCH TÊN CÔNG TƠ GELEX Ở ĐÂY
    match_ten = re.search(r'Tên công tơ.*?([A-Za-z0-9\-]+)', text_all)
    data["ten_cong_to"] = match_ten.group(1) if match_ten else "GELEX"

    # lan_cai_dat = Số lần lập trình (Dùng để giao diện sắp xếp TRƯỚC/SAU)
    match_sl = re.search(r'Số lần lập trình\s*(\d+)', text_all)
    data["lan_cai_dat"] = int(match_sl.group(1)) if match_sl else 0

    # ngay_lap_trinh = Thời gian cài đặt
    match_tg = re.search(r'Thời gian lập trình cuối\s*([\d/: ]+)', text_all)
    data["ngay_lap_trinh"] = match_tg.group(1).strip() if match_tg else "N/A"

    # Cấp thêm TU/TI mặc định cho GELEX để không bị lỗi
    data["tu"] = "1.0"
    data["ti"] = "1.0"

    # --- KHUNG GIỜ THỰC TẾ (Chia làm Ngày thường và Chủ nhật) ---
    match_ngay1 = re.search(r'Ngày 1\s*(.*?)(?:\nNgày 2|$)', text_all, re.DOTALL)
    data["thuc_te_nt"] = phan_tich_khung_gio_gelex(match_ngay1.group(1).strip()) if match_ngay1 else {'T1': [], 'T2': [], 'T3': []}

    match_ngay2 = re.search(r'Ngày 2\s*(.*?)(?:\nCấu hình tuần|$)', text_all, re.DOTALL)
    data["thuc_te_cn"] = phan_tich_khung_gio_gelex(match_ngay2.group(1).strip()) if match_ngay2 else {'T1': [], 'T2': [], 'T3': []}

    # --- CHẤM ĐIỂM TT16 / TT60 (So sánh trên Ngày thường) ---
    khung_gio_dict = data["thuc_te_nt"]
    
    tt16_t1 = ['04:00-09:30', '11:30-17:00', '20:00-22:00']
    tt16_t2 = ['09:30-11:30', '17:00-20:00']
    tt16_t3 = ['00:00-04:00', '22:00-24:00']
    
    tt60_t1 = ['06:00-17:30', '22:30-24:00']
    tt60_t2 = ['17:30-22:30']
    tt60_t3 = ['00:00-06:00']

    t1 = khung_gio_dict.get('T1', [])
    t2 = khung_gio_dict.get('T2', [])
    t3 = khung_gio_dict.get('T3', [])

    data['is_tt16'] = (t1 == tt16_t1) and (t2 == tt16_t2) and (t3 == tt16_t3)
    data['is_tt60'] = (t1 == tt60_t1) and (t2 == tt60_t2) and (t3 == tt60_t3)

    # --- CÁC BỘ CHỈ SỐ P GIAO ---
    data["p_giao"] = lay_chi_so_theo_obis(text_all, r'1\.8\.0')
    data["b1_giao"] = lay_chi_so_theo_obis(text_all, r'1\.8\.1')
    data["b2_giao"] = lay_chi_so_theo_obis(text_all, r'1\.8\.2')
    data["b3_giao"] = lay_chi_so_theo_obis(text_all, r'1\.8\.3')

    # --- CÁC BỘ CHỈ SỐ P NHẬN ---
    data["p_nhan"] = lay_chi_so_theo_obis(text_all, r'2\.8\.0')
    data["b1_nhan"] = lay_chi_so_theo_obis(text_all, r'2\.8\.1')
    data["b2_nhan"] = lay_chi_so_theo_obis(text_all, r'2\.8\.2')
    data["b3_nhan"] = lay_chi_so_theo_obis(text_all, r'2\.8\.3')

    # --- CHỈ SỐ VÔ CÔNG ---
    data["q_giao"] = lay_chi_so_theo_obis(text_all, r'3\.8\.0')
    data["q_nhan"] = lay_chi_so_theo_obis(text_all, r'4\.8\.0')

    return data