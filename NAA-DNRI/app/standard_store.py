import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STANDARDS_FILE = os.path.join(DATA_DIR, "standards.json")


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(STANDARDS_FILE):
		with open(STANDARDS_FILE, "w", encoding="utf-8") as f:
			json.dump({"next_id": 1, "standards": []}, f, ensure_ascii=False, indent=2)


def _read() -> Dict[str, Any]:
	_ensure_store()
	with open(STANDARDS_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _write(data: Dict[str, Any]) -> None:
	with open(STANDARDS_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def list_standards() -> List[Dict[str, Any]]:
	"""Get all standards"""
	return _read().get("standards", [])


def list_standards_paginated(page: int = 1, per_page: int = 20, standard_type: Optional[str] = None) -> tuple[List[Dict[str, Any]], int, int]:
	"""Get paginated standards with optional type filter. Returns (standards, total_pages, total_count)"""
	all_standards = _read().get("standards", [])
	
	# Filter by standard type if specified
	if standard_type:
		all_standards = [s for s in all_standards if s.get("standard_type", "").lower() == standard_type.lower()]
	
	total_count = len(all_standards)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Calculate offset
	offset = (page - 1) * per_page
	
	# Get standards for current page
	standards = all_standards[offset:offset + per_page]
	
	return standards, total_pages, total_count


def create_standard(
	standard_name: str,
	box_name: str,
	weight: float,
	moisture: float = 0,
	note: str = ""
) -> int:
	"""Create a new standard record"""
	data = _read()
	standard_id = data["next_id"]
	
	# Calculate corrected weight (weight - moisture weight)
	moisture_weight = weight * (moisture / 100) if moisture > 0 else 0
	corrected_weight = weight - moisture_weight
	
	standard = {
		"id": standard_id,
		"standard_name": standard_name,
		"box_name": box_name,
		"weight": weight,
		"moisture": moisture,
		"corrected_weight": corrected_weight,
		"closing_date": datetime.now().strftime("%Y-%m-%d"),
		"note": note,
		"created_at": datetime.now().isoformat()
	}
	
	data["standards"].append(standard)
	data["next_id"] += 1
	_write(data)
	
	return standard_id


def get_standard(standard_id: int) -> Optional[Dict[str, Any]]:
	"""Get a specific standard by ID"""
	standards = list_standards()
	for standard in standards:
		if standard["id"] == standard_id:
			return standard
	return None


def update_standard(
	standard_id: int,
	standard_name: str,
	box_name: str,
	weight: float,
	moisture: float = 0,
	note: str = ""
) -> bool:
	"""Update an existing standard"""
	data = _read()
	for standard in data["standards"]:
		if standard["id"] == standard_id:
			# Calculate corrected weight
			moisture_weight = weight * (moisture / 100) if moisture > 0 else 0
			corrected_weight = weight - moisture_weight
			
			standard["standard_name"] = standard_name
			standard["box_name"] = box_name
			standard["weight"] = weight
			standard["moisture"] = moisture
			standard["corrected_weight"] = corrected_weight
			standard["note"] = note
			
			_write(data)
			return True
	return False


def delete_standard(standard_id: int) -> bool:
	"""Delete a standard"""
	data = _read()
	data["standards"] = [s for s in data["standards"] if s["id"] != standard_id]
	_write(data)
	return True


def export_standards_to_excel() -> str:
	"""Export standards to Excel format"""
	import io
	import pandas as pd
	
	standards = list_standards()
	
	# Create DataFrame
	df = pd.DataFrame(standards)
	
	# Reorder columns for better display
	column_order = [
		"id", "standard_name", "box_name", "weight", "moisture", 
		"corrected_weight", "closing_date", "note"
	]
	
	# Only include columns that exist in the data
	available_columns = [col for col in column_order if col in df.columns]
	df = df[available_columns]
	
	# Rename columns to Vietnamese
	column_names = {
		"id": "ID",
		"standard_name": "Tên mẫu chuẩn",
		"box_name": "Tên box",
		"weight": "Khối lượng (g)",
		"moisture": "Độ ẩm (%)",
		"corrected_weight": "Khối lượng hiệu chỉnh (g)",
		"closing_date": "Ngày đóng",
		"note": "Ghi chú"
	}
	
	df = df.rename(columns=column_names)
	
	# Create Excel file in memory
	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Mẫu chuẩn đã đóng', index=False)
	
	output.seek(0)
	return output.getvalue()


def import_standards_from_csv(csv_content: str) -> tuple[int, List[str]]:
	"""Import standards from CSV content. Returns (success_count, error_messages)"""
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
			'Tên mẫu chuẩn': 'standard_name',
			'Tên box': 'box_name',
			'Khối lượng (g)': 'weight',
			'Độ ẩm (%)': 'moisture',
			'Ghi chú': 'note'
		}
		
		# Map Vietnamese headers to English field names
		mapped_header = []
		for col in header:
			mapped_header.append(field_mapping.get(col, col))
		
		# Debug: Check if mapping worked
		required_fields = ['standard_name', 'box_name', 'standard_type', 'weight']
		for field in required_fields:
			if field not in mapped_header:
				# Map back to Vietnamese for error message
				vi_names = {
					'standard_name': 'Tên mẫu chuẩn',
					'box_name': 'Tên box',
					'standard_type': 'Loại mẫu chuẩn',
					'weight': 'Khối lượng (g)'
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
			if not row.get('standard_name') or not row.get('box_name') or not row.get('weight'):
				errors.append(f"Dòng {i}: Thiếu thông tin bắt buộc")
				continue
			
			try:
				# Parse weight and moisture
				weight = float(row.get('weight', 0))
				moisture = float(row.get('moisture', 0)) if row.get('moisture') else 0
				
				# Create standard
				create_standard(
					standard_name=row['standard_name'],
					box_name=row['box_name'],
					weight=weight,
					moisture=moisture,
					note=row.get('note', '')
				)
				success_count += 1
			except Exception as e:
				errors.append(f"Dòng {i}: Lỗi tạo mẫu chuẩn - {str(e)}")
				
	except Exception as e:
		errors.append(f"Lỗi đọc file CSV: {str(e)}")
	
	return success_count, errors
