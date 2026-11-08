import pdfplumber
import re
from datetime import datetime

# 1. HÀM CHỐNG LỖI ĐA DẤU CHẤM (Đã ngon)
def xu_ly_chi_so_elster(text_so):
    try:
        if not text_so: return 0
        text_so = text_so.strip()
        last_dot = text_so.rfind('.')
        last_comma = text_so.rfind(',')
        last_separator = max(last_dot, last_comma)
        if last_separator != -1:
            temp_str = list(text_so)
            temp_str[last_separator] = 'D'
            text_so = "".join(temp_str)
            text_so = text_so.replace('.', '').replace(',', '')
            text_so = text_so.replace('D', '.')
        return int(float(text_so) / 1000)
    except Exception:
        return 0

def phan_tich_khung_gio(text_day):
    moc_gio = re.findall(r"(\d{2}:\d{2})\s+(Rate\d)", text_day)
    if not moc_gio: return {}
    ket_qua = {'T1': [], 'T2': [], 'T3': []}
    mapping = {'Rate1': 'T1', 'Rate2': 'T2', 'Rate3': 'T3'}
    if moc_gio and moc_gio[0][0] != '00:00':
        last_rate = moc_gio[-1][1]
        loai_bieu_last = mapping.get(last_rate)
        if loai_bieu_last:
            ket_qua[loai_bieu_last].append(f"00:00-{moc_gio[0][0]}")
    for i in range(len(moc_gio)):
        start_time = moc_gio[i][0]
        rate_raw = moc_gio[i][1]
        loai_bieu = mapping.get(rate_raw)
        if i < len(moc_gio) - 1: end_time = moc_gio[i+1][0]
        else: end_time = "24:00"
        if loai_bieu: ket_qua[loai_bieu].append(f"{start_time}-{end_time}")
    return ket_qua

# 2. HÀM XỬ LÝ NGÀY THÁNG THÔNG MINH (Bao thầu cả AM/PM lẫn SA/CH)
def viet_hoa_ngay_thang(chuoi_ngay_goc):
    try:
        chuoi = chuoi_ngay_goc.strip()
        # Ép chữ SA/CH của Việt Nam thành AM/PM cho Python dễ hiểu
        chuoi_chuan = chuoi.replace('SA', 'AM').replace('CH', 'PM').replace('sa', 'AM').replace('ch', 'PM')
        
        # Kịch bản 1: Thử đọc theo kiểu Mỹ (Tháng/Ngày/Năm)
        try:
            dt = datetime.strptime(chuoi_chuan, "%m/%d/%Y %I:%M %p")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass
            
        # Kịch bản 2: Thử đọc theo kiểu Châu Âu/Việt Nam (Ngày/Tháng/Năm)
        try:
            dt = datetime.strptime(chuoi_chuan, "%d/%m/%Y %I:%M %p")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass

        # Kịch bản 3: Thử đọc kiểu 24 giờ không có Sáng Chiều
        try:
            dt = datetime.strptime(chuoi_chuan, "%d/%m/%Y %H:%M")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass
            
        return chuoi_ngay_goc # Trả về gốc nếu dị quá không đọc được
    except Exception:
        return chuoi_ngay_goc

def xu_ly_file_elster(file_pdf):
    toan_bo_text = ""
    with pdfplumber.open(file_pdf) as pdf:
        for page in pdf.pages:
            toan_bo_text += page.extract_text() + "\n"

    serial = re.search(r"New serial number\s+[\-]*(\d+)", toan_bo_text)
    serial = serial.group(1) if serial else "N/A"
    match_ten_elster = re.search(r'(A1700)', toan_bo_text)
    ten_cong_to = "ELSTER " + match_ten_elster.group(1) if match_ten_elster else "ELSTER"
    tu = re.search(r"VT\s+[\d\.]+\s+[\d\.]+\s+=\s+([\d\.]+)", toan_bo_text)
    tu = tu.group(1) if tu else "1.0"
    ti = re.search(r"CT\s+[\d\.]+\s+[\d\.]+\s+=\s+([\d\.]+)", toan_bo_text)
    ti = ti.group(1) if ti else "1.0"
    
    # 3. FIX CỤM TÌM KIẾM LOGIC (Chấp mọi loại chữ cái đằng sau giờ)
    prog_log = re.search(r"Count\s+TimeStamp.*?\n\s*(\d+)\s+([\d/]+\s+[\d:]+(?:\s+[a-zA-Z]+)?)", toan_bo_text)
    so_lan = int(prog_log.group(1)) if prog_log else 0
    ngay_lap_trinh_goc = prog_log.group(2) if prog_log else "N/A"
    ngay_lap_trinh = viet_hoa_ngay_thang(ngay_lap_trinh_goc) if ngay_lap_trinh_goc != "N/A" else "N/A"

    vi_tri_current = toan_bo_text.find("Current Values")
    txt_cs = toan_bo_text[vi_tri_current:] if vi_tri_current != -1 else toan_bo_text

    p_giao = re.search(r"([\d\,\.]+)\s+Import Wh", txt_cs)
    b1_giao = re.search(r"1\s+([\d\,\.]+)\s+Import Wh", txt_cs)
    b2_giao = re.search(r"2\s+([\d\,\.]+)\s+Import Wh", txt_cs)
    b3_giao = re.search(r"3\s+([\d\,\.]+)\s+Import Wh", txt_cs)

    p_nhan = re.search(r"([\d\,\.]+)\s+Export Wh", txt_cs)
    b1_nhan = re.search(r"4\s+([\d\,\.]+)\s+Export Wh", txt_cs)
    b2_nhan = re.search(r"5\s+([\d\,\.]+)\s+Export Wh", txt_cs)
    b3_nhan = re.search(r"6\s+([\d\,\.]+)\s+Export Wh", txt_cs)

    q_giao = re.search(r"([\d\,\.]+)\s+CD 1", txt_cs)
    q_nhan = re.search(r"([\d\,\.]+)\s+CD 2", txt_cs)

    day_blocks = re.findall(r"Day Number \d+\s*Switching time Active rate\(s\)\s*(.*?)(?=Day Number \d+|Tariff Checksum|Meter Constants)", toan_bo_text, re.DOTALL | re.IGNORECASE)
    
    is_tt60, is_tt16 = False, False
    thuc_te_nt, thuc_te_cn = {'T1': [], 'T2': [], 'T3': []}, {'T1': [], 'T2': [], 'T3': []}
    
    if len(day_blocks) >= 2:
        thuc_te_nt = phan_tich_khung_gio(day_blocks[0].strip())
        thuc_te_cn = phan_tich_khung_gio(day_blocks[1].strip())
        TT60_NT = {'T1': ['06:00-17:30', '22:30-24:00'], 'T2': ['17:30-22:30'], 'T3': ['00:00-06:00']}
        TT60_CN = {'T1': ['06:00-24:00'], 'T2': [], 'T3': ['00:00-06:00']}
        TT16_NT = {'T1': ['04:00-09:30', '11:30-17:00', '20:00-22:00'], 'T2': ['09:30-11:30', '17:00-20:00'], 'T3': ['00:00-04:00', '22:00-24:00']}
        TT16_CN = {'T1': ['04:00-22:00'], 'T2': [], 'T3': ['00:00-04:00', '22:00-24:00']}
        is_tt60 = (thuc_te_nt == TT60_NT) and (thuc_te_cn == TT60_CN)
        is_tt16 = (thuc_te_nt == TT16_NT) and (thuc_te_cn == TT16_CN)

    return {
        "ten_cong_to": ten_cong_to,
        "serial": serial, 
        "tu": tu, 
        "ti": ti, 
        "lan_cai_dat": so_lan, 
        "ngay_lap_trinh": ngay_lap_trinh,
        "p_giao": xu_ly_chi_so_elster(p_giao.group(1)) if p_giao else 0,
        "b1_giao": xu_ly_chi_so_elster(b1_giao.group(1)) if b1_giao else 0,
        "b2_giao": xu_ly_chi_so_elster(b2_giao.group(1)) if b2_giao else 0,
        "b3_giao": xu_ly_chi_so_elster(b3_giao.group(1)) if b3_giao else 0,
        "p_nhan": xu_ly_chi_so_elster(p_nhan.group(1)) if p_nhan else 0,
        "b1_nhan": xu_ly_chi_so_elster(b1_nhan.group(1)) if b1_nhan else 0,
        "b2_nhan": xu_ly_chi_so_elster(b2_nhan.group(1)) if b2_nhan else 0,
        "b3_nhan": xu_ly_chi_so_elster(b3_nhan.group(1)) if b3_nhan else 0,
        "q_giao": xu_ly_chi_so_elster(q_giao.group(1)) if q_giao else 0,
        "q_nhan": xu_ly_chi_so_elster(q_nhan.group(1)) if q_nhan else 0,
        "is_tt60": is_tt60, 
        "is_tt16": is_tt16,
        "thuc_te_nt": thuc_te_nt, 
        "thuc_te_cn": thuc_te_cn
    }