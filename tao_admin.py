from ketnoi import ket_noi
from werkzeug.security import generate_password_hash

try:
    conn = ket_noi()
    cursor = conn.cursor()

    # Kiểm tra tài khoản Admin đã tồn tại chưa
    cursor.execute(
        "SELECT id FROM taikhoan WHERE username = %s",
        ("admin",)
    )

    admin = cursor.fetchone()

    if admin:
        print("Tài khoản Admin đã tồn tại!")

    else:
        # Mã hóa mật khẩu
        mat_khau = generate_password_hash("Admin@123")

        sql = """
            INSERT INTO taikhoan
            (ma_sv, ho_ten, username, password, quyen)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            None,
            "Quản trị viên",
            "admin",
            mat_khau,
            "admin"
        ))

        conn.commit()

        print("Tạo tài khoản Admin thành công!")

    cursor.close()
    conn.close()

except Exception as e:
    print("Có lỗi xảy ra:", e)