import os
import mysql.connector

def ket_noi():
    host = os.getenv("DB_HOST", "localhost")

    cau_hinh = {
        "host": host,
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "Bethihongdiem711"),
        "database": os.getenv("DB_NAME", "quanlylaodog"),
        "port": int(os.getenv("DB_PORT", "3306"))
    }

    # Nếu kết nối đến TiDB Cloud thì sử dụng SSL
    if host != "localhost":
        cau_hinh["ssl_ca"] = os.path.join(
            os.path.dirname(__file__), "ca.pem"
        )
        cau_hinh["ssl_verify_cert"] = True
        cau_hinh["ssl_verify_identity"] = True

    return mysql.connector.connect(**cau_hinh)