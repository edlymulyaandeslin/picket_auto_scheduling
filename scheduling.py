#!/usr/bin/env python3

import sys
from api import generate_and_save_schedule, get_schedule_by_week

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("="*50)
		print("\nFormat Penggunaan:")
		print("  python scheduling.py week <nomor_minggu> [jumlah_per_hari]")
		print("  python scheduling.py check <nomor_minggu>\n")
		print("="*50)
		sys.exit()

	command = sys.argv[1].lower()

	if command == "week":
		if len(sys.argv) < 3:
			print("❌ Error: Nomor minggu wajib diisi!")
			print("Contoh: python scheduling.py week 1 [3]")
			sys.exit()

		try:
			week_num = int(sys.argv[2])
		except ValueError:
			print("❌ Error: Nomor minggu harus berupa angka (integer)!")
			sys.exit()

		# Menangkap jumlah siswa per hari jika diinput (default 2 jika kosong)
		per_day = 2
		if len(sys.argv) > 3:
			try:
				per_day = int(sys.argv[3])
				if per_day < 1:
					print("❌ Error: Jumlah per hari minimal 1 orang!")
					sys.exit()
			except ValueError:
				print("❌ Error: Jumlah per hari harus berupa angka (integer)!")
				sys.exit()

		print(f"\nSedang memproses jadwal untuk Minggu ke-{week_num} ({per_day} orang/hari)...")
		result_message = generate_and_save_schedule(target_week=week_num, students_per_day=per_day)
		print(result_message)

	elif command == "check":
		if len(sys.argv) < 3:
			print("❌ Error: Nomor minggu yang ingin dicek wajib diisi!")
			print("Contoh: python scheduling.py check 1")
			sys.exit()

		try:
			week_num = int(sys.argv[2])
		except ValueError:
			print("❌ Error: Nomor minggu harus berupa angka (integer)!")
			sys.exit()

		result_message = get_schedule_by_week(target_week=week_num)
		print(result_message)

	else:
		print(f"Perintah '{command}' tidak dikenal.")
		print("Gunakan: week <nomor_minggu> [jumlah_per_hari] atau check <nomor_minggu>")
