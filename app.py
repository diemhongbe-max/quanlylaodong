
from flask import Flask, render_template, request, redirect, url_for, session, flash
from ketnoi import ket_noi
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "qlld_secret_key_2026"


# =====================================
# 1. TRANG ĐĂNG NHẬP
# =====================================

@app.route("/", methods=["GET", "POST"])
def dang_nhap():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = ket_noi()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM taikhoan
            WHERE username = %s
        """, (username,))

        tai_khoan = cursor.fetchone()

        cursor.close()
        conn.close()

        if tai_khoan and check_password_hash(
            tai_khoan["password"], password
        ):

            session["id"] = tai_khoan["id"]
            session["username"] = tai_khoan["username"]
            session["ho_ten"] = tai_khoan["ho_ten"]
            session["quyen"] = tai_khoan["quyen"]
            session["ma_sv"] = tai_khoan["ma_sv"]

            if tai_khoan["quyen"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("thanh_vien"))

        flash("Tên đăng nhập hoặc mật khẩu không đúng!")

    return render_template("dangnhap.html")


# =====================================
# 2. TRANG QUẢN TRỊ ADMIN
# =====================================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "id" not in session or session["quyen"] != "admin":
        return redirect(url_for("dang_nhap"))

    tab = request.args.get("tab", "congviec")

    if tab not in ["congviec", "sinhvien", "phancong"]:
        tab = "congviec"

    conn = ket_noi()
    cursor = conn.cursor(dictionary=True)

    # ---------------------------------
    # THÊM CÔNG VIỆC
    # ---------------------------------

    if request.method == "POST" and request.form.get("hanh_dong") == "them_cong_viec":

        ten_cv = request.form["ten_cv"].strip()
        mo_ta = request.form.get("mo_ta", "").strip()
        ngay_lam = request.form["ngay_lam"]

        try:
            cursor.execute("""
                INSERT INTO congviec (ten_cv, mo_ta, ngay_lam)
                VALUES (%s, %s, %s)
            """, (ten_cv, mo_ta, ngay_lam))

            conn.commit()
            flash("Thêm công việc thành công!")

        except Exception as e:
            conn.rollback()
            flash("Không thể thêm công việc: " + str(e))

        cursor.close()
        conn.close()

        return redirect(url_for("admin", tab="congviec"))

    # ---------------------------------
    # THÊM SINH VIÊN
    # ---------------------------------

    if request.method == "POST" and request.form.get("hanh_dong") == "them_sinh_vien":

        ma_sv = request.form["ma_sv"].strip()
        ho_ten = request.form["ho_ten"].strip()
        lop = request.form["lop"].strip()

        try:
            cursor.execute("""
                INSERT INTO sinhvien (ma_sv, ho_ten, lop)
                VALUES (%s, %s, %s)
            """, (ma_sv, ho_ten, lop))

            conn.commit()
            flash("Thêm sinh viên thành công!")

        except Exception as e:
            conn.rollback()
            flash("Không thể thêm sinh viên: " + str(e))

        cursor.close()
        conn.close()

        return redirect(url_for("admin", tab="sinhvien"))

    # ---------------------------------
    # PHÂN CÔNG CÔNG VIỆC
    # ---------------------------------

    if request.method == "POST" and request.form.get("hanh_dong") == "phan_cong":

        ma_cv = request.form.get("ma_cv")
        ds_ma_sv = request.form.getlist("ma_sv")

        if not ma_cv or not ds_ma_sv:
            flash("Vui lòng chọn công việc và ít nhất một sinh viên!")

        else:
            try:
                # Kiểm tra công việc có tồn tại không
                cursor.execute("""
                    SELECT ma_cv FROM congviec
                    WHERE ma_cv = %s
                """, (ma_cv,))

                if not cursor.fetchone():
                    raise ValueError("Công việc không tồn tại!")

                # Kiểm tra sinh viên có tồn tại không
                placeholders = ",".join(["%s"] * len(ds_ma_sv))

                cursor.execute(
                    f"""
                    SELECT ma_sv FROM sinhvien
                    WHERE ma_sv IN ({placeholders})
                    """,
                    tuple(ds_ma_sv)
                )

                ma_sv_hop_le = [
                    sv["ma_sv"] for sv in cursor.fetchall()
                ]

                if len(ma_sv_hop_le) != len(set(ds_ma_sv)):
                    raise ValueError("Có sinh viên không tồn tại!")

                # Phân công cho từng sinh viên
                for ma_sv in ma_sv_hop_le:

                    # Tránh phân công trùng
                    cursor.execute("""
                        SELECT id FROM phancong
                        WHERE ma_sv = %s AND ma_cv = %s
                    """, (ma_sv, ma_cv))

                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO phancong
                            (ma_sv, ma_cv, trang_thai)
                            VALUES (%s, %s, %s)
                        """, (ma_sv, ma_cv, "Chưa hoàn thành"))

                conn.commit()
                flash("Phân công lao động thành công!")

            except Exception as e:
                conn.rollback()
                flash("Không thể phân công: " + str(e))

        cursor.close()
        conn.close()

        return redirect(url_for("admin", tab="phancong"))

    # ---------------------------------
    # LẤY DANH SÁCH SINH VIÊN
    # ---------------------------------

    cursor.execute("""
        SELECT ma_sv, ho_ten, lop
        FROM sinhvien
        ORDER BY ma_sv
    """)

    danh_sach_sv = cursor.fetchall()

    # ---------------------------------
    # LẤY DANH SÁCH CÔNG VIỆC
    # ---------------------------------

    cursor.execute("""
        SELECT ma_cv, ten_cv, mo_ta, ngay_lam
        FROM congviec
        ORDER BY ma_cv DESC
    """)

    danh_sach_cv = cursor.fetchall()

    # ---------------------------------
    # LẤY DANH SÁCH PHÂN CÔNG
    # MỖI CÔNG VIỆC KÈM CÁC SINH VIÊN
    # ---------------------------------

    cursor.execute("""
        SELECT
            cv.ma_cv,
            cv.ten_cv,
            cv.ngay_lam,
            GROUP_CONCAT(
                CONCAT(sv.ma_sv, ' - ', sv.ho_ten)
                ORDER BY sv.ma_sv
                SEPARATOR ', '
            ) AS sinh_vien
        FROM congviec cv
        LEFT JOIN phancong pc
            ON cv.ma_cv = pc.ma_cv
        LEFT JOIN sinhvien sv
            ON pc.ma_sv = sv.ma_sv
        GROUP BY
            cv.ma_cv,
            cv.ten_cv,
            cv.ngay_lam
        ORDER BY cv.ma_cv DESC
    """)

    danh_sach_phan_cong = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        danh_sach_sv=danh_sach_sv,
        danh_sach_cv=danh_sach_cv,
        danh_sach_phan_cong=danh_sach_phan_cong,
        tab=tab
    )


# =====================================
# 3. SỬA THÔNG TIN SINH VIÊN
# =====================================

@app.route("/sua-sinh-vien/<ma_sv>", methods=["GET", "POST"])
def sua_sinh_vien(ma_sv):

    if "id" not in session or session["quyen"] != "admin":
        return redirect(url_for("dang_nhap"))

    conn = ket_noi()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        ho_ten = request.form["ho_ten"].strip()
        lop = request.form["lop"].strip()

        try:
            cursor.execute("""
                UPDATE sinhvien
                SET ho_ten = %s, lop = %s
                WHERE ma_sv = %s
            """, (ho_ten, lop, ma_sv))

            conn.commit()
            flash("Cập nhật sinh viên thành công!")

        except Exception as e:
            conn.rollback()
            flash("Không thể sửa sinh viên: " + str(e))

        cursor.close()
        conn.close()

        return redirect(url_for("admin", tab="sinhvien"))

    cursor.execute("""
        SELECT * FROM sinhvien
        WHERE ma_sv = %s
    """, (ma_sv,))

    sinh_vien = cursor.fetchone()

    cursor.close()
    conn.close()

    if sinh_vien is None:
        flash("Không tìm thấy sinh viên!")
        return redirect(url_for("admin", tab="sinhvien"))

    return render_template(
        "sua_sinhvien.html",
        sv=sinh_vien
    )


# =====================================
# 4. XÓA SINH VIÊN
# =====================================

@app.route("/xoa-sinh-vien/<ma_sv>", methods=["POST"])
def xoa_sinh_vien(ma_sv):

    if "id" not in session or session["quyen"] != "admin":
        return redirect(url_for("dang_nhap"))

    conn = ket_noi()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM sinhvien
            WHERE ma_sv = %s
        """, (ma_sv,))

        conn.commit()

        if cursor.rowcount > 0:
            flash("Xóa sinh viên thành công!")
        else:
            flash("Không tìm thấy sinh viên!")

    except Exception:
        conn.rollback()
        flash("Không thể xóa sinh viên vì sinh viên đang có phân công!")

    cursor.close()
    conn.close()

    return redirect(url_for("admin", tab="sinhvien"))


# =====================================
# 5. TRANG THÀNH VIÊN
# =====================================

@app.route("/thanh-vien")
def thanh_vien():

    if "id" not in session or session["quyen"] != "thanhvien":
        return redirect(url_for("dang_nhap"))

    ma_sv = session.get("ma_sv")

    if not ma_sv:
        flash("Tài khoản chưa được liên kết với sinh viên!")
        return redirect(url_for("dang_xuat"))

    conn = ket_noi()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT ma_sv, ho_ten, lop
        FROM sinhvien
        WHERE ma_sv = %s
    """, (ma_sv,))

    sinh_vien = cursor.fetchone()

    cursor.execute("""
        SELECT
            cv.ma_cv,
            cv.ten_cv,
            cv.mo_ta,
            cv.ngay_lam,
            pc.trang_thai
        FROM phancong pc
        JOIN congviec cv ON pc.ma_cv = cv.ma_cv
        WHERE pc.ma_sv = %s
        ORDER BY cv.ngay_lam ASC
    """, (ma_sv,))

    danh_sach_cv = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "thanhvien.html",
        sv=sinh_vien,
        danh_sach_cv=danh_sach_cv
    )


# =====================================
# 6. ĐĂNG XUẤT
# =====================================

@app.route("/dang-xuat")
def dang_xuat():

    session.clear()

    return redirect(url_for("dang_nhap"))


# =====================================
# CHẠY CHƯƠNG TRÌNH
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
