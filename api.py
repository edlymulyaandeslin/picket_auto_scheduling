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

def generate_and_save_schedule(target_week, students_per_day=5):
	"""Mengacak dan menyimpan jadwal piket, memastikan 5 orang per hari 
	dan tidak ada student_id yang sama pada hari yang sama (siswa boleh bertugas >1 kali seminggu)."""

	# 1. Cek duplikasi minggu di database
	if check_week_exists(target_week):
		return f"❌ Gagal: Jadwal untuk Minggu ke-{target_week} sudah ada di database! Tidak boleh duplikat."

	students = get_students()
	if not students:
		return "❌ Data siswa kosong!"

	days = ["senin", "selasa", "rabu", "kamis", "jumat"]
	total_slots = len(days) * students_per_day # 5 hari * 5 orang = 25 slot

	# 2. Buat pool siswa dan gandakan jika total siswa kurang dari total slot yang dibutuhkan
	pool_students = students.copy()
	while len(pool_students) < total_slots:
		pool_students.extend(students)

	# 3. Acak urutan pool siswa secara keseluruhan
	random.shuffle(pool_students)

	conn = get_connection()
	if not conn:
		return "❌ Gagal terhubung ke database!"

	try:
		with conn.cursor() as cursor:
			for i, day in enumerate(days):
				# Ambil 5 siswa untuk hari tersebut dari pool yang sudah diacak
				start_idx = i * students_per_day
				end_idx = start_idx + students_per_day
				daily_students = pool_students[start_idx:end_idx]

				# Set untuk memastikan di hari yang SAMA tidak ada student_id yang kembar
				seen_student_ids = set()

				for student in daily_students:
					s_id = student["id"]

					# Jika dalam 1 hari yang sama id-nya sudah masuk, cari pengganti dari sisa pool
					# (Mencegah duplikat internal pada hari tersebut)
					while s_id in seen_student_ids:
						# Ambil elemen acak lain dari pool utama untuk mengganti yang duplikat
						replacement = random.choice(pool_students)
						while replacement["id"] in seen_student_ids:
							replacement = random.choice(pool_students)
						student = replacement
						s_id = student["id"]

					seen_student_ids.add(s_id)

					sql = "INSERT INTO schedules (student_id, week, day) VALUES (%s, %s, %s)"
					cursor.execute(sql, (s_id, target_week, day))

			conn.commit()

			success_msg = f"🎉 Sukses! Jadwal Minggu ke-{target_week} ({students_per_day} orang/hari) berhasil dibuat & disimpan."
			details = get_schedule_by_week(target_week)
			return f"{success_msg}\n{details}"

	except Exception as e:
		conn.rollback()
		return f"❌ Terjadi error: {e}"
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
