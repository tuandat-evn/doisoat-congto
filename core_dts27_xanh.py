import pdfplumber
import re
from datetime import datetime
def lay_chi_so_dts27_xanh(text_clean, obis):
    pattern = obis.replace('.', r'\.') + r'[\s\,\n]*([\d\.]+)'
    match = re.search(pattern, text_clean)
    if match:
        try:
            return float(match.group(1)) / 1000.0
        except:
            return 0
    return 0

def phan_tich_khung_gio(matches, target_day):
    day_matches = [m for m in matches if m[0] == target_day]
    day_matches.sort(key=lambda x: x[1])
    
    res = {'T1': [], 'T2': [], 'T3': []}
    if not day_matches: return res
    
    for i in range(len(day_matches)):
        start_time = day_matches[i][1][:5]
        tariff = 'T' + day_matches[i][2]
        end_time = day_matches[i+1][1][:5] if i < len(day_matches) - 1 else '24:00'
        if start_time != end_time:
            res[tariff].append(f"{start_time}-{end_time}")
    return res

def xu_ly_file_dts27_xanh(file_path):
    data = {"tu": "1.0", "ti": "1.0", "ten_cong_to": "DTS27 XANH"}
    with pdfplumber.open(file_path) as pdf:
        text_all = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    text_clean = text_all.replace('"', '')

    # --- THÔNG TIN CƠ BẢN ---
    match_so = re.search(r'Meter number:[\s\,\n]*(\d+)', text_clean, re.IGNORECASE)
    data["serial"] = match_so.group(1) if match_so else "N/A"

    match_sl = re.search(r'Number Of Configuration Program.*?Changes.*?0\.0\.96\.2\.0\.255[\s\,\n]*(\d+)', text_clean, re.DOTALL | re.IGNORECASE)
    data["lan_cai_dat"] = int(match_sl.group(1)) if match_sl else 0

    match_tg = re.search(r'The Latest Programming Date and.*?Time.*?0\.0\.96\.2\.1\.255[\s\,\n]*([\d\- \:]+)', text_clean, re.DOTALL | re.IGNORECASE)
    if match_tg:
        try:
            # Ép từ YYYY-MM-DD sang DD/MM/YYYY
            dt_obj = datetime.strptime(match_tg.group(1).strip(), "%Y-%m-%d %H:%M:%S")
            data["ngay_lap_trinh"] = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
        except:
            data["ngay_lap_trinh"] = match_tg.group(1).strip()
    else:
        data["ngay_lap_trinh"] = "N/A"

    # --- KHUNG GIỜ ---
    matches_gio = re.findall(r'\b([12])[\s\,\n]+([\d]{2}:[\d]{2}:[\d]{2})[\s\,\n]+([123])\b', text_clean)
    
    data["thuc_te_nt"] = phan_tich_khung_gio(matches_gio, '1')
    data["thuc_te_cn"] = phan_tich_khung_gio(matches_gio, '2')

    # --- CHẤM ĐIỂM TT16 / TT60 ---
    tt16_t1, tt16_t2, tt16_t3 = ['04:00-09:30', '11:30-17:00', '20:00-22:00'], ['09:30-11:30', '17:00-20:00'], ['00:00-04:00', '22:00-24:00']
    tt60_t1, tt60_t2, tt60_t3 = ['06:00-17:30', '22:30-24:00'], ['17:30-22:30'], ['00:00-06:00']

    t1, t2, t3 = data["thuc_te_nt"].get('T1', []), data["thuc_te_nt"].get('T2', []), data["thuc_te_nt"].get('T3', [])
    data['is_tt16'] = (t1 == tt16_t1) and (t2 == tt16_t2) and (t3 == tt16_t3)
    data['is_tt60'] = (t1 == tt60_t1) and (t2 == tt60_t2) and (t3 == tt60_t3)

    # --- CHỈ SỐ P & Q ---
    data["p_giao"] = lay_chi_so_dts27_xanh(text_clean, '1.0.1.8.0.255')
    data["b1_giao"] = lay_chi_so_dts27_xanh(text_clean, '1.0.1.8.1.255')
    data["b2_giao"] = lay_chi_so_dts27_xanh(text_clean, '1.0.1.8.2.255')
    data["b3_giao"] = lay_chi_so_dts27_xanh(text_clean, '1.0.1.8.3.255')
    data["p_nhan"] = lay_chi_so_dts27_xanh(text_clean, '1.0.2.8.0.255')
    data["b1_nhan"] = lay_chi_so_dts27_xanh(text_clean, '1.0.2.8.1.255')
    data["b2_nhan"] = lay_chi_so_dts27_xanh(text_clean, '1.0.2.8.2.255')
    data["b3_nhan"] = lay_chi_so_dts27_xanh(text_clean, '1.0.2.8.3.255')
    data["q_giao"] = lay_chi_so_dts27_xanh(text_clean, '1.0.3.8.0.255')
    data["q_nhan"] = lay_chi_so_dts27_xanh(text_clean, '1.0.4.8.0.255')

    return data