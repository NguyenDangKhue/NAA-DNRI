import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FOILS_FILE = os.path.join(DATA_DIR, "foils.json")


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(FOILS_FILE):
		with open(FOILS_FILE, "w", encoding="utf-8") as f:
			json.dump({"next_id": 1, "foils": []}, f, ensure_ascii=False, indent=2)


def _read() -> Dict[str, Any]:
	_ensure_store()
	with open(FOILS_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _write(data: Dict[str, Any]) -> None:
	with open(FOILS_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def list_foils() -> List[Dict[str, Any]]:
	"""Get all foils"""
	return _read().get("foils", [])


def list_foils_paginated(page: int = 1, per_page: int = 20, foil_type: Optional[str] = None) -> tuple[List[Dict[str, Any]], int, int]:
	"""Get paginated foils with optional type filter. Returns (foils, total_pages, total_count)"""
	all_foils = _read().get("foils", [])
	
	# Filter by foil type if specified
	if foil_type:
		all_foils = [f for f in all_foils if f.get("foil_type", "").lower() == foil_type.lower()]
	
	total_count = len(all_foils)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Calculate offset
	offset = (page - 1) * per_page
	
	# Get foils for current page
	foils = all_foils[offset:offset + per_page]
	
	return foils, total_pages, total_count


def create_foil(
	foil_code: str,
	foil_type: str,
	weight: float,
	note: str = ""
) -> int:
	"""Create a new foil record"""
	data = _read()
	foil_id = data["next_id"]
	
	foil = {
		"id": foil_id,
		"foil_code": foil_code,
		"foil_type": foil_type,
		"weight": weight,
		"closing_date": datetime.now().strftime("%Y-%m-%d"),
		"note": note,
		"created_at": datetime.now().isoformat()
	}
	
	data["foils"].append(foil)
	data["next_id"] += 1
	_write(data)
	
	return foil_id


def get_foil(foil_id: int) -> Optional[Dict[str, Any]]:
	"""Get a specific foil by ID"""
	foils = list_foils()
	for foil in foils:
		if foil["id"] == foil_id:
			return foil
	return None


def update_foil(
	foil_id: int,
	foil_code: str,
	foil_type: str,
	weight: float,
	note: str = ""
) -> bool:
	"""Update an existing foil"""
	data = _read()
	for foil in data["foils"]:
		if foil["id"] == foil_id:
			foil["foil_code"] = foil_code
			foil["foil_type"] = foil_type
			foil["weight"] = weight
			foil["note"] = note
			
			_write(data)
			return True
	return False


def delete_foil(foil_id: int) -> bool:
	"""Delete a foil"""
	data = _read()
	data["foils"] = [f for f in data["foils"] if f["id"] != foil_id]
	_write(data)
	return True


def export_foils_to_excel() -> str:
	"""Export foils to Excel format"""
	import io
	import pandas as pd
	
	foils = list_foils()
	
	# Create DataFrame
	df = pd.DataFrame(foils)
	
	# Reorder columns for better display
	column_order = [
		"id", "foil_code", "foil_type", "weight", 
		"closing_date", "note"
	]
	
	# Only include columns that exist in the data
	available_columns = [col for col in column_order if col in df.columns]
	df = df[available_columns]
	
	# Rename columns to Vietnamese
	column_names = {
		"id": "ID",
		"foil_code": "Mã lá dò",
		"foil_type": "Loại lá dò",
		"weight": "Khối lượng (mg)",
		"closing_date": "Ngày đóng",
		"note": "Ghi chú"
	}
	
	df = df.rename(columns=column_names)
	
	# Create Excel file in memory
	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Lá dò đã đóng', index=False)
	
	output.seek(0)
	return output.getvalue()


def import_foils_from_csv(csv_content: str) -> tuple[int, List[str]]:
	"""Import foils from CSV content. Returns (success_count, error_messages)"""
	import csv
	import io
	from datetime import datetime
	
	errors = []
	success_count = 0
	
	try:
		# Use proper CSV parsing with StringIO
		csv_reader = csv.reader(io.StringIO(csv_content))
		rows = list(csv_reader)
		
		if len(rows) < 2:
			errors.append("File CSV phải có ít nhất 1 dòng dữ liệu")
			return 0, errors
		
		# Get header and map Vietnamese to English field names
		header = [col.strip() for col in rows[0]]
		
		# Remove BOM (Byte Order Mark) from first column if present
		if header and header[0].startswith('\ufeff'):
			header[0] = header[0][1:]  # Remove BOM character
		
		field_mapping = {
			'Mã lá dò': 'foil_code',
			'Loại lá dò': 'foil_type',
			'Khối lượng (mg)': 'weight',
			'Ngày đóng': 'closing_date',
			'Ghi chú': 'note'
		}
		
		# Map Vietnamese headers to English field names
		mapped_header = []
		for col in header:
			mapped_header.append(field_mapping.get(col, col))
		
		# Debug: Check if mapping worked
		required_fields = ['foil_code', 'foil_type', 'weight']
		for field in required_fields:
			if field not in mapped_header:
				# Map back to Vietnamese for error message
				vi_names = {
					'foil_code': 'Mã lá dò',
					'foil_type': 'Loại lá dò',
					'weight': 'Khối lượng (mg)'
				}
				errors.append(f"Thiếu cột bắt buộc: {vi_names.get(field, field)}")
				return 0, errors
		
		# Process data rows
		for i, row_data in enumerate(rows[1:], 2):
			if not any(row_data):  # Skip empty rows
				continue
				
			if len(row_data) != len(header):
				errors.append(f"Dòng {i}: Số cột không khớp với header")
				continue
			
			# Create row dict with mapped field names
			row = dict(zip(mapped_header, [val.strip() for val in row_data]))
			
			# Validate required fields
			if not row.get('foil_code') or not row.get('foil_type') or not row.get('weight'):
				errors.append(f"Dòng {i}: Thiếu thông tin bắt buộc")
				continue
			
			try:
				# Parse weight
				weight = float(row.get('weight', 0))
				
				# Create foil
				create_foil(
					foil_code=row['foil_code'],
					foil_type=row['foil_type'],
					weight=weight,
					note=row.get('note', '')
				)
				success_count += 1
			except Exception as e:
				errors.append(f"Dòng {i}: Lỗi tạo lá dò - {str(e)}")
				
	except Exception as e:
		errors.append(f"Lỗi đọc file CSV: {str(e)}")
	
	return success_count, errors
