
from ketnoi import ket_noi
from werkzeug.security import generate_password_hash

try:
    conn = ket_noi()
    cursor = conn.cursor()

    ma_sv = "SV01"
    ho_ten = "Nguyễn Văn An"
    username = "sv01"
    password = generate_password_hash("123456")

    # Kiểm tra sinh viên đã tồn tại chưa
    cursor.execute(
        "SELECT ma_sv FROM sinhvien WHERE ma_sv = %s",
        (ma_sv,)
    )

    sinh_vien = cursor.fetchone()

    if sinh_vien is None:
        print("Không tìm thấy SV01 trong bảng sinhvien!")
    else:
        # Kiểm tra tài khoản đã tồn tại chưa
        cursor.execute(
            "SELECT id FROM taikhoan WHERE username = %s",
            (username,)
        )

        tai_khoan = cursor.fetchone()

        if tai_khoan:
            # Cập nhật tài khoản cũ
            cursor.execute("""
                UPDATE taikhoan
                SET ma_sv = %s,
                    ho_ten = %s,
                    password = %s,
                    quyen = %s
                WHERE username = %s
            """, (
                ma_sv, ho_ten, password,
                "thanhvien", username
            ))

        else:
            # Tạo tài khoản mới
            cursor.execute("""
                INSERT INTO taikhoan
                (ma_sv, ho_ten, username, password, quyen)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                ma_sv, ho_ten, username,
                password, "thanhvien"
            ))

        conn.commit()
        print("Tạo/cập nhật tài khoản thành công!")

    cursor.close()
    conn.close()

except Exception as e:
    print("Có lỗi:", e)
