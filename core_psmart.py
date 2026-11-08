import pdfplumber
import re
from datetime import datetime

def lay_chi_so_psmart(text_clean, obis):
    # Thêm re.DOTALL để quét xuyên qua các dòng bị ngắt
    pattern = obis.replace('.', r'\.') + r'.*?\$?([\d\.]+)\s*[\*\^\{\}\$]*\s*k[vVwW]'
    match = re.search(pattern, text_clean, re.IGNORECASE | re.DOTALL)
    if match:
        try: return float(match.group(1))
        except: return 0
    return 0

def phan_tich_khung_gio_psmart(matches, target_day):
    day_matches = [m for m in matches if m[0] == target_day]
    day_matches.sort(key=lambda x: x[1])
    
    res = {'T1': [], 'T2': [], 'T3': []}
    if not day_matches: return res
    
    for i in range(len(day_matches)):
        time_str = day_matches[i][1]
        start_time = f"{time_str[:2]}:{time_str[2:]}"
        tariff = 'T' + day_matches[i][2]
        
        if i < len(day_matches) - 1:
            next_time = day_matches[i+1][1]
            end_time = f"{next_time[:2]}:{next_time[2:]}"
        else:
            end_time = '24:00'
            
        if start_time != end_time:
            res[tariff].append(f"{start_time}-{end_time}")
    return res

def xu_ly_file_psmart(file_path):
    data = {"tu": "1.0", "ti": "1.0", "ten_cong_to": "PSMART"}
    with pdfplumber.open(file_path) as pdf:
        text_all = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    text_clean = text_all.replace('"', '')
    # Ép "siêu nén": Xóa sạch toàn bộ dấu cách, xuống dòng, dấu phẩy để trị đám chữ bị chèn ngang
    text_compact = re.sub(r'[\s\,\"\']+', '', text_all)

    # --- THÔNG TIN CƠ BẢN ---
    match_so = re.search(r'No:\s*(\d+)', text_clean, re.IGNORECASE)
    if not match_so:
        match_so = re.search(r'0\.0\.0\.0\.0.*?(\d{8,})', text_clean)
    data["serial"] = match_so.group(1) if match_so else "N/A"

    match_sl = re.search(r'0\.0\.C\.2\.0.*?\(([\d]+)\)', text_clean)
    data["lan_cai_dat"] = int(match_sl.group(1)) if match_sl else 0

    # Trị Ngày lập trình bị ngắt dòng: Ép loại bỏ mọi ký tự không phải số
    match_tg_block = re.search(r'0\.0\.C\.2\.1\(\).*?\((.*?)\)', text_clean, re.DOTALL)
    if match_tg_block:
        raw_time = re.sub(r'\D', '', match_tg_block.group(1)) 
        if len(raw_time) >= 12:
            try:
                dt_obj = datetime.strptime(raw_time[:12], "%y%m%d%H%M%S")
                data["ngay_lap_trinh"] = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
            except:
                data["ngay_lap_trinh"] = raw_time[:12]
        else:
            data["ngay_lap_trinh"] = "N/A"
    else:
        data["ngay_lap_trinh"] = "N/A"

    # --- KHUNG GIỜ ---
    # Dùng bản siêu nén để lờ đi các chữ rác như "calendar" hoặc "day_profile"
    # Dao găm "vét máng" mọi trường hợp sai chính tả (DayId, Dayld...) và ký tự rác
    matches_gio = re.findall(r'[Dd]ay[^:\d]*(\d):\(([\d]{4})\)[^\d\(\)]*?T\(([123])\)', text_compact, re.IGNORECASE)
    
    data["thuc_te_nt"] = phan_tich_khung_gio_psmart(matches_gio, '1')
    data["thuc_te_cn"] = phan_tich_khung_gio_psmart(matches_gio, '2')

    # --- CHẤM ĐIỂM TT16 / TT60 ---
    tt16_t1, tt16_t2, tt16_t3 = ['04:00-09:30', '11:30-17:00', '20:00-22:00'], ['09:30-11:30', '17:00-20:00'], ['00:00-04:00', '22:00-24:00']
    tt60_t1, tt60_t2, tt60_t3 = ['06:00-17:30', '22:30-24:00'], ['17:30-22:30'], ['00:00-06:00']

    t1, t2, t3 = data["thuc_te_nt"].get('T1', []), data["thuc_te_nt"].get('T2', []), data["thuc_te_nt"].get('T3', [])
    data['is_tt16'] = (t1 == tt16_t1) and (t2 == tt16_t2) and (t3 == tt16_t3)
    data['is_tt60'] = (t1 == tt60_t1) and (t2 == tt60_t2) and (t3 == tt60_t3)

    # --- CHỈ SỐ P & Q ---
    data["p_giao"] = lay_chi_so_psmart(text_clean, '1.0.1.8.0')
    data["b1_giao"] = lay_chi_so_psmart(text_clean, '1.0.1.8.1')
    data["b2_giao"] = lay_chi_so_psmart(text_clean, '1.0.1.8.2')
    data["b3_giao"] = lay_chi_so_psmart(text_clean, '1.0.1.8.3')
    data["p_nhan"] = lay_chi_so_psmart(text_clean, '1.0.2.8.0')
    data["b1_nhan"] = lay_chi_so_psmart(text_clean, '1.0.2.8.1')
    data["b2_nhan"] = lay_chi_so_psmart(text_clean, '1.0.2.8.2')
    data["b3_nhan"] = lay_chi_so_psmart(text_clean, '1.0.2.8.3')
    data["q_giao"] = lay_chi_so_psmart(text_clean, '1.0.3.8.0')
    data["q_nhan"] = lay_chi_so_psmart(text_clean, '1.0.4.8.0')

    return data