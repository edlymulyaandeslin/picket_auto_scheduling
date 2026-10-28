#!/usr/bin/env python3

import random
# Asumsikan fungsi get_students() mengembalikan list of dict dari database
# Contoh: [{'id': 1, 'name': 'Budi', ...}, {'id': 2, 'name': 'Ani', ...}, ...]
from api import get_students

# 1. Ambil data siswa dari database
students = get_students()

# Validasi: Pastikan jumlah siswa cukup (misal minimal 10)
if len(students) < 10:
  print(
      "Peringatan: Jumlah siswa kurang dari 10, pembagian mungkin tidak pas."
  )

days = ["senin", "selasa", "rabu", "kamis", "jumat"]
week = 1

# 2. Acak urutan siswa secara random (supaya tidak urut berdasarkan ID/abjad)
random.shuffle(students)

# 3. Bagi siswa secara merata ke dalam 5 hari (2 orang per hari)
# Kita bisa pakai teknik slicing list Python
schedule_list = []
chunk_size = len(students) // len(days)  # 10 / 5 = 2 orang per hari

for i, day in enumerate(days):
  # Ambil 2 siswa untuk setiap hari
  start_idx = i * chunk_size
  end_idx = start_idx + chunk_size
  daily_students = students[start_idx:end_idx]

  # Simpan ke struktur data jadwal
  for student in daily_students:
    schedule_list.append({
        "week": week,
        "day": day,
        "student_id": student["id"],
        "student_name": student["name"],
        "gender": student["gender"]
    })

# 4. Tampilkan hasil generate jadwal piket minggu ini
print(f"\n=== JADWAL PIKET MINGGU KE-{week} ===")
for day in days:
  print(f"\nHari {day.capitalize()}:")
  # Filter siswa yang bertugas di hari tersebut
  workers = [s for s in schedule_list if s["day"] == day]
  for w in workers:
    print(f" - {w['student_name']} ({w['gender']})")

