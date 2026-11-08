import pdfplumber
import re
from datetime import datetime

def phan_tich_khung_gio_vinasino(text_block):
    res = {'T1': [], 'T2': [], 'T3': []}
    if not text_block: return res
    
    # Bắt mốc giờ (VD: 06:00 17:30 01)
    matches = re.findall(r'(\d{2}:\d{2})[\s\n]+(\d{2}:\d{2})[\s\n]+0?([123])', text_block)
    
    for m in matches:
        t1, t2, tariff_num = m[0], m[1], m[2]
        tariff = 'T' + tariff_num
        
        # Thuật toán thông minh phân biệt "0h sáng" và "0h đêm"
        if t2 == '00:00':
            start, end = t1, '24:00'
        elif t1 == '00:00':
            # Nếu mốc thứ 2 là buổi tối (VD: 22:30) => Chắc chắn là giờ đêm (22:30 - 24:00)
            if int(t2[:2]) > 12:
                start, end = t2, '24:00'
            # Nếu mốc thứ 2 là buổi sáng (VD: 04:00, 06:00) => Giờ sáng bình thường (00:00 - 06:00)
            else:
                start, end = '00:00', t2
        else:
            start, end = t1, t2
            
        res[tariff].append(f"{start}-{end}")
        
    # Sắp xếp và xóa các block ảo (nếu có)
    for k in res:
        res[k] = list(set([item for item in res[k] if item.split('-')[0] != item.split('-')[1]]))
        res[k].sort()
    return res

def get_index_vinasino(text_compact, keyword):
    pattern = keyword + r'.*?([\d\.]+)\s*k[VvWw]'
    m = re.search(pattern, text_compact, re.IGNORECASE)
    if m:
        try: return float(m.group(1))
        except: return 0
    return 0

def xu_ly_file_vinasino(file_path):
    data = {"tu": "1.0", "ti": "1.0", "ten_cong_to": "VINASINO"}
    with pdfplumber.open(file_path) as pdf:
        text_all = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    text_clean = text_all.replace('"', '')
    text_compact = re.sub(r'[\r\n]+', ' ', text_clean) # Ép văn bản nằm trên 1 dòng để quét chỉ số

    # --- THÔNG TIN CƠ BẢN ---
    match_loai = re.search(r'Công tơ.*?(VSE[\w\-]+)', text_clean, re.IGNORECASE)
    if match_loai:
        data["ten_cong_to"] = f"VINASINO ({match_loai.group(1).upper()})"

    # Cắt bỏ các số 0 vô nghĩa ở đầu ID
    match_so = re.search(r'ID Công tơ:\s*0*(\d+)', text_clean, re.IGNORECASE)
    data["serial"] = match_so.group(1) if match_so else "N/A"

    match_sl = re.search(r'Ghi nhận sự kiện cài đặt.*?(\d+)\s*\(lần\)', text_compact, re.IGNORECASE)
    data["lan_cai_dat"] = int(match_sl.group(1)) if match_sl else 0

    # Quét tóm ngày giờ cài đặt (dù nó đứng trước hay đứng sau)
    match_tg = re.search(r'Ghi nhận sự kiện cài đặt.*?(?:(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})|(\d{2}:\d{2})\s*(\d{2}/\d{2}/\d{4}))', text_compact, re.IGNORECASE)
    if match_tg:
        if match_tg.group(1): # Format: DD/MM/YYYY HH:MM
            data["ngay_lap_trinh"] = f"{match_tg.group(1)} {match_tg.group(2)}:00"
        else:                 # Format: HH:MM DD/MM/YYYY
            data["ngay_lap_trinh"] = f"{match_tg.group(4)} {match_tg.group(3)}:00"
    else:
        data["ngay_lap_trinh"] = "N/A"

    # --- CHỈ SỐ P & Q ---
    data["p_giao"] = get_index_vinasino(text_compact, 'hữu công giao tổng')
    data["b1_giao"] = get_index_vinasino(text_compact, 'hữu công giao 1')
    data["b2_giao"] = get_index_vinasino(text_compact, 'hữu công giao 2')
    data["b3_giao"] = get_index_vinasino(text_compact, 'hữu công giao 3')
    data["p_nhan"] = get_index_vinasino(text_compact, 'hữu công nhận tổng')
    data["b1_nhan"] = get_index_vinasino(text_compact, 'hữu công nhận 1')
    data["b2_nhan"] = get_index_vinasino(text_compact, 'hữu công nhận 2')
    data["b3_nhan"] = get_index_vinasino(text_compact, 'hữu công nhận 3')
    data["q_giao"] = get_index_vinasino(text_compact, 'vô công giao tổng')
    data["q_nhan"] = get_index_vinasino(text_compact, 'vô công nhận tổng')

    # --- KHUNG GIỜ ---
    # Cắt đôi lấy Bảng 1 (Ngày thường) và Bảng 2 (Chủ nhật)
    block_nt_match = re.search(r'Bảng BG ngày thường \(bảng 1\)(.*?)Bảng BG ngày thường \(bảng 2\)', text_clean, re.DOTALL | re.IGNORECASE)
    block_cn_match = re.search(r'Bảng BG ngày thường \(bảng 2\)(.*)', text_clean, re.DOTALL | re.IGNORECASE)
    
    data["thuc_te_nt"] = phan_tich_khung_gio_vinasino(block_nt_match.group(1) if block_nt_match else "")
    data["thuc_te_cn"] = phan_tich_khung_gio_vinasino(block_cn_match.group(1) if block_cn_match else "")

    # --- CHẤM ĐIỂM TT16 / TT60 ---
    tt16_t1, tt16_t2, tt16_t3 = ['04:00-09:30', '11:30-17:00', '20:00-22:00'], ['09:30-11:30', '17:00-20:00'], ['00:00-04:00', '22:00-24:00']
    tt60_t1, tt60_t2, tt60_t3 = ['06:00-17:30', '22:30-24:00'], ['17:30-22:30'], ['00:00-06:00']

    t1, t2, t3 = data["thuc_te_nt"].get('T1', []), data["thuc_te_nt"].get('T2', []), data["thuc_te_nt"].get('T3', [])
    data['is_tt16'] = (t1 == tt16_t1) and (t2 == tt16_t2) and (t3 == tt16_t3)
    data['is_tt60'] = (t1 == tt60_t1) and (t2 == tt60_t2) and (t3 == tt60_t3)

    return data