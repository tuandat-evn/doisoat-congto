import pdfplumber
import re
from datetime import datetime

def phan_tich_khung_gio_hhm(text_clean):
    # Lấy riêng khu vực Biểu giá đang hoạt động
    block_match = re.search(r'Biểu giá đang hoạt động(.*?)Biểu giá dự phòng', text_clean, re.DOTALL | re.IGNORECASE)
    block = block_match.group(1) if block_match else text_clean
    
    # Bắt tất cả các mốc giờ và biểu giá (VD: 00:00#T3)
    matches = re.findall(r'(\d{2}:\d{2})#T([123])', block, re.IGNORECASE)
    
    dt_groups = []
    current_group = []
    last_time = -1
    
    for m in matches:
        time_str = m[0]
        tariff = 'T' + m[1]
        # Quy đổi giờ ra phút để so sánh
        minutes = int(time_str[:2]) * 60 + int(time_str[3:])
        
        # Lập trình thông minh: Nếu giờ bị lùi lại hoặc reset về 0 => Chuyển sang lịch Chủ Nhật (DT2)
        if minutes <= last_time:
            dt_groups.append(current_group)
            current_group = []
        
        current_group.append((time_str, tariff))
        last_time = minutes
        
    if current_group:
        dt_groups.append(current_group)
        
    def group_to_dict(group):
        res = {'T1': [], 'T2': [], 'T3': []}
        if not group: return res
        for i in range(len(group)):
            start_time = group[i][0]
            tariff = group[i][1]
            end_time = group[i+1][0] if i < len(group) - 1 else '24:00'
            if start_time != end_time:
                res[tariff].append(f"{start_time}-{end_time}")
        return res

    thuc_te_nt = group_to_dict(dt_groups[0] if len(dt_groups) > 0 else [])
    thuc_te_cn = group_to_dict(dt_groups[1] if len(dt_groups) > 1 else [])
    
    return thuc_te_nt, thuc_te_cn

def get_index_hhm(text_compact, obis, unit='Wh'):
    # Khóa vùng quét, bắt đúng số trước chữ Wh/varh và tự động CHIA 1000
    pattern = obis.replace('.', r'\.') + r'[^Wv]*?(\d+)' + unit
    m = re.search(pattern, text_compact, re.IGNORECASE)
    if m:
        try: 
            return float(m.group(1)) / 1000
        except: 
            return 0
    return 0

def xu_ly_file_hhm(file_path):
    data = {"tu": "1.0", "ti": "1.0", "ten_cong_to": "HHM"}
    with pdfplumber.open(file_path) as pdf:
        text_all = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    text_clean = text_all.replace('"', '')
    text_compact = re.sub(r'[\s\,\"\']+', '', text_all) # Ép siêu nén để quét chỉ số

    # --- THÔNG TIN CƠ BẢN ---
    # Bắt chính xác mã công tơ (VD: HHM-38GT)
    match_loai = re.search(r'công tơ:\s*([A-Z0-9\-]+)', text_clean, re.IGNORECASE)
    if match_loai:
        data["ten_cong_to"] = match_loai.group(1).upper()

    match_so = re.search(r'S[ôố] chế tạo:\s*(\d+)', text_clean, re.IGNORECASE)
    data["serial"] = match_so.group(1) if match_so else "N/A"

    match_sl = re.search(r'Số lần lập trình.*?(\d+)', text_clean, re.IGNORECASE | re.DOTALL)
    data["lan_cai_dat"] = int(match_sl.group(1)) if match_sl else 0

    match_tg = re.search(r'Ngày và thời gian lập trình cuối.*?(\d{2}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})', text_clean, re.IGNORECASE | re.DOTALL)
    if match_tg:
        try:
            dt_obj = datetime.strptime(match_tg.group(1).strip(), "%y-%m-%d %H:%M:%S")
            data["ngay_lap_trinh"] = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
        except:
            data["ngay_lap_trinh"] = match_tg.group(1).strip()
    else:
        data["ngay_lap_trinh"] = "N/A"

    # --- CHỈ SỐ P & Q ---
    data["p_giao"] = get_index_hhm(text_compact, '1.8.0', 'Wh')
    data["b1_giao"] = get_index_hhm(text_compact, '1.8.1', 'Wh')
    data["b2_giao"] = get_index_hhm(text_compact, '1.8.2', 'Wh')
    data["b3_giao"] = get_index_hhm(text_compact, '1.8.3', 'Wh')
    data["p_nhan"] = get_index_hhm(text_compact, '2.8.0', 'Wh')
    data["b1_nhan"] = get_index_hhm(text_compact, '2.8.1', 'Wh')
    data["b2_nhan"] = get_index_hhm(text_compact, '2.8.2', 'Wh')
    data["b3_nhan"] = get_index_hhm(text_compact, '2.8.3', 'Wh')
    data["q_giao"] = get_index_hhm(text_compact, '3.8.0', 'varh')
    data["q_nhan"] = get_index_hhm(text_compact, '4.8.0', 'varh')

    # --- KHUNG GIỜ ---
    thuc_te_nt, thuc_te_cn = phan_tich_khung_gio_hhm(text_clean)
    data["thuc_te_nt"] = thuc_te_nt
    data["thuc_te_cn"] = thuc_te_cn

    # --- CHẤM ĐIỂM TT16 / TT60 ---
    tt16_t1, tt16_t2, tt16_t3 = ['04:00-09:30', '11:30-17:00', '20:00-22:00'], ['09:30-11:30', '17:00-20:00'], ['00:00-04:00', '22:00-24:00']
    tt60_t1, tt60_t2, tt60_t3 = ['06:00-17:30', '22:30-24:00'], ['17:30-22:30'], ['00:00-06:00']

    t1, t2, t3 = data["thuc_te_nt"].get('T1', []), data["thuc_te_nt"].get('T2', []), data["thuc_te_nt"].get('T3', [])
    data['is_tt16'] = (t1 == tt16_t1) and (t2 == tt16_t2) and (t3 == tt16_t3)
    data['is_tt60'] = (t1 == tt60_t1) and (t2 == tt60_t2) and (t3 == tt60_t3)

    return data