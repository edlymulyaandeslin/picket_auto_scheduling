import random
from db import get_connection


def get_students():
	conn = get_connection()
	if not conn:
		return

	try:
		with conn.cursor() as cursor:
			query = "SELECT * FROM students"
			cursor.execute(query)
			result = cursor.fetchall()

			if not result:
				print("Belum ada student.")
		return result

	finally:
		conn.close()

def get_detail_student(conn, id):
	try:
		with conn.cursor() as cursor:
			query = "SELECT * FROM students WHERE id = %s"
			cursor.execute(query, (id,))
			result = cursor.fetchone()

			return result
	except Exception as e:
		return None

def insert():
	conn = get_connection()
	if not conn:
		return
	while True:
		name = input("Masukkan nama siswa: ")
		gender = input("Pilih gender (L/P): ")

		if name and gender and gender.upper() in ("L", "P"):
			break

		print("Data yang anda masukkan tidak valid!")
		print("Silakan periksa lagi!")

	try:
		with conn.cursor() as cursor:
			query = "INSERT INTO students (name, gender) VALUES(%s, %s)"
			cursor.execute(query, (name, gender))
			conn.commit()
			print(f"Berhasil menambahkan {name}!")
	except Exception as e:
		print(f"Gagal insert data. ERROR: {e}")
	finally:
		conn.close()

def update(id):
	conn = get_connection()
	if not conn:
		return

	student = get_detail_student(conn, id)
	if not student:
		print(f"Student tidak ditemukan!")
		return

	new_name = input("Masukkan nama baru: ")
	new_gender = input("Masukkan gender terbaru (L/P): ")

	if not new_name:
		new_name = student['name']
	if not new_gender:
		new_gender = student['gender']

	try:
		with conn.cursor() as cursor:
			query = "UPDATE students SET name=%s, gender=%s WHERE id=%s"
			cursor.execute(query, (new_name, new_gender, id))
			conn.commit()

			return True
	except Exception as e:
		print(f"Update data gagal. ERROR: {e}")
		return False
	finally:
		conn.close()


def delete(id):
	conn = get_connection()
	if not conn:
		return

	student = get_detail_student(conn, id)
	if not student:
		print(f"Student tidak ditemukan!")
		return

	try:
		with conn.cursor() as cursor:
			query = "DELETE FROM students WHERE id=%s"
			cursor.execute(query, (id,))
			conn.commit()

			return True
	except Exception as e:
		print(f"Gagal delete. ERROR: {e}")
		return False
	finally:
		conn.close()

def check_week_exists(target_week):
	"""Mengecek apakah jadwal untuk minggu tersebut sudah ada di database"""
	conn = get_connection()
	if not conn:
		return False
	try:
		with conn.cursor() as cursor:
			sql = "SELECT COUNT(*) as total FROM schedules WHERE week = %s"
			cursor.execute(sql, (target_week,))
			result = cursor.fetchone()
			return result["total"] > 0
	finally:
		conn.close()

def generate_and_save_schedule(target_week=1):
	"""Mengacak dan menyimpan jadwal piket secara merata ke database"""
	# 1. Cek duplikasi di database
	if check_week_exists(target_week):
		return (
			f"Gagal: Jadwal untuk Minggu ke-{target_week} sudah ada di database!"
			" Tidak boleh duplikat."
		)


	students = get_students()

	if not students:
		return "Data siswa kosong!"

	days = ["senin", "selasa", "rabu", "kamis", "jumat"]
	random.shuffle(students)  # Acak urutan siswa

	conn = get_connection()
	if not conn:
		return "Gagal terhubung ke database!"

	try:
		with conn.cursor() as cursor:
			chunk_size = len(students) // len(days)  # 10 siswa / 5 hari = 2 orang/hari

			for i, day in enumerate(days):
				start_idx = i * chunk_size
				end_idx = start_idx + chunk_size
				daily_students = students[start_idx:end_idx]

				for student in daily_students:
					sql = (
						"INSERT INTO schedules (student_id, week, day) VALUES (%s, %s,"
						" %s)"
					)
					cursor.execute(sql, (student["id"], target_week, day))

			conn.commit()
			# Panggil fungsi get_schedule_by_week untuk langsung menampilkan hasilnya
			success_msg = f"🎉 Sukses! Jadwal piket untuk Minggu ke-{target_week} berhasil dibuat & disimpan."
			details = get_schedule_by_week(target_week)
			return f"{success_msg}\n{details}"
	except Exception as e:
		conn.rollback()
		return f"Terjadi error: {e}"
	finally:
 		conn.close()

def get_schedule_by_week(target_week):
	"""Mengambil dan menampilkan jadwal piket berdasarkan nomor minggu"""
	conn = get_connection()
	if not conn:
		return "❌ Gagal terhubung ke database!"

	try:
		with conn.cursor() as cursor:
			sql = """
				SELECT s.id AS student_id, st.name, st.gender, s.day 
				FROM schedules s
				JOIN students st ON s.student_id = st.id
				WHERE s.week = %s
				ORDER BY FIELD(s.day, 'senin', 'selasa', 'rabu', 'kamis', 'jumat')
			"""
			cursor.execute(sql, (target_week,))
			result = cursor.fetchall()

			if not result:
				return f"⚠️ Tidak ada jadwal ditemukan untuk Minggu ke-{target_week}."

			days = ["senin", "selasa", "rabu", "kamis", "jumat"]
			output = [f"\n=== JADWAL PIKET MINGGU KE-{target_week} ==="]

			for day in days:
				workers = [r for r in result if r["day"] == day]
				output.append(f"\nHari {day.capitalize()}:")
				if not workers:
					output.append("  - (Tidak ada petugas)")
				else:
					for w in workers:
						output.append(f"  - {w['name']} ({w['gender']})")

			output.append("-" * 40)
			return "\n".join(output)

	except Exception as e:
		return f"❌ Terjadi error: {e}"
	finally:
		conn.close()
