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
	"""Mengacak dan menyimpan jadwal piket (Senin-Sabtu),
	memastikan setiap siswa mendapat tepat 3x dalam seminggu dan tidak ada duplikat di hari yang sama."""

	# 1. Cek duplikasi minggu di database
	if check_week_exists(target_week):
		return f"❌ Gagal: Jadwal untuk Minggu ke-{target_week} sudah ada di database! Tidak boleh duplikat."

	students = get_students()
	if not students:
		return "❌ Data siswa kosong!"

	days = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]
	total_slots = len(days) * students_per_day # 6 hari * 5 orang = 30 slot
	total_students = len(students) # Biasanya 10 orang

	# Validasi: Total slot harus pas dengan (total_siswa * 3)
	if total_slots != total_students * 3:
		return (
			f"❌ Gagal: Total slot ({total_slots}) tidak cocok dengan aturan 3x seminggu "
			f"untuk {total_students} siswa (dibutuhkan tepat {total_students * 3} slot)."
		)

	conn = get_connection()
	if not conn:
		return "❌ Gagal terhubung ke database!"

	try:
		with conn.cursor() as cursor:
			# 2. Buat master list pool: setiap siswa dimasukkan tepat 3 kali ke dalam list
			master_pool = []
			for s in students:
				master_pool.extend([s] * 3) # 10 siswa * 3 = 30 elemen

			# Acak urutan pool agar distribusinya acak dan adil
			random.shuffle(master_pool)

			# 3. Distribusikan ke 6 hari (masing-masing 5 orang) dengan memastikan 
			# tidak ada student_id yang kembar di hari yang sama.
			for day in days:
				daily_students = []
				seen_today = set()

				# Ambil 5 siswa unik untuk hari ini dari master_pool
				i = 0
				while len(daily_students) < students_per_day and i < len(master_pool):
					candidate = master_pool[i]
					if candidate["id"] not in seen_today:
						daily_students.append(candidate)
						seen_today.add(candidate["id"])
						# Tandai elemen ini agar tidak diambil lagi di hari ini
						master_pool.pop(i)
					else:
						i += 1
				
				# Jika karena suatu hal sisa pool kurang (jarang terjadi jika angka pas), 
				# ambil dari sisa apa adanya
				if len(daily_students) < students_per_day and master_pool:
					for candidate in list(master_pool):
						if candidate["id"] not in seen_today and len(daily_students) < students_per_day:
							daily_students.append(candidate)
							seen_today.add(candidate["id"])
							master_pool.remove(candidate)

				# Insert ke database untuk hari tersebut
				for student in daily_students:
					sql = "INSERT INTO schedules (student_id, week, day) VALUES (%s, %s, %s)"
					cursor.execute(sql, (student["id"], target_week, day))

			conn.commit()

			success_msg = f"🎉 Sukses! Jadwal Minggu ke-{target_week} (Senin-Sabtu, 5 orang/hari, masing-masing tepat 3x/minggu) berhasil dibuat & disimpan."
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
				ORDER BY FIELD(s.day, 'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu')
			"""
			cursor.execute(sql, (target_week,))
			result = cursor.fetchall()

			if not result:
				return f"⚠️ Tidak ada jadwal ditemukan untuk Minggu ke-{target_week}."

			days = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu"]
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
