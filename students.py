#!/usr/bin/env python3

import sys
from api import get_students, insert, update, delete

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("="*50)
		print("Format Penggunaan:")
		print(" ./students.py get")
		print(" ./students.py insert")
		print(" ./students.py update <ID>")
		print(" ./students.py delete <ID>")
		print("="*50)
		sys.exit()

	command = sys.argv[1].lower()

	if command == "get":
		result = get_students()
		for no, student in enumerate(result, start=1):
			print(f"{no}. ID [{student['id']}]: {student['name']}")
	elif command == "insert":
		insert()
	elif command == "update":
		if len(sys.argv) < 3:
			print("="*50)
			print("Format Penggunaan:")
			print("./students.py update <ID>")
			print("="*50)
			sys.exit()

		id = sys.argv[2]
		success = update(id)
		if success:
			print(f"Data Student ID {id} berhasil diperbarui!")
	elif command == "delete":
		if len(sys.argv) < 3:
			print("="*50)
			print("Format Penggunaan:")
			print("./students.py delete <ID>")
			print("="*50)
			sys.exit()

		id = sys.argv[2]
		success = delete(id)
		if success:
			print(f"Student Id {id} berhasil dihapus!")

	else:
		print("Format perintah salah!")
