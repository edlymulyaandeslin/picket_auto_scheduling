import pymysql

# Konfigurasi database sentral
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "whoami",  # Ganti password MariaDB kamu
    "database": "picket_schedule",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
  """Fungsi global untuk membuka koneksi ke database"""
  try:
    conn = pymysql.connect(**DB_CONFIG)
    return conn
  except Exception as e:
    print(f"Koneksi database gagal: {e}")
    return None
