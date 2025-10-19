import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CLOSED_SAMPLES_FILE = os.path.join(DATA_DIR, "closed_samples.json")


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(CLOSED_SAMPLES_FILE):
		with open(CLOSED_SAMPLES_FILE, "w", encoding="utf-8") as f:
			json.dump({"next_id": 1, "closed_samples": []}, f, ensure_ascii=False, indent=2)


def _read() -> Dict[str, Any]:
	_ensure_store()
	with open(CLOSED_SAMPLES_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _write(data: Dict[str, Any]) -> None:
	with open(CLOSED_SAMPLES_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def list_closed_samples() -> List[Dict[str, Any]]:
	"""Get all closed samples"""
	return _read().get("closed_samples", [])


def list_closed_samples_paginated(page: int = 1, per_page: int = 20, customer_name: Optional[str] = None) -> tuple[List[Dict[str, Any]], int, int]:
	"""Get paginated closed samples with optional customer filter. Returns (samples, total_pages, total_count)"""
	all_samples = _read().get("closed_samples", [])
	
	# Filter by customer name if specified
	if customer_name:
		all_samples = [s for s in all_samples if s.get("customer_name", "").lower() == customer_name.lower()]
	
	total_count = len(all_samples)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Calculate offset
	offset = (page - 1) * per_page
	
	# Get samples for current page
	samples = all_samples[offset:offset + per_page]
	
	return samples, total_pages, total_count


def create_closed_sample(
	closing_date: str,
	customer_name: str,
	sample_name: str,
	encoding: str,
	box_symbol: str,
	weight: float,
	moisture: float,
	note: str = ""
) -> int:
	"""Create a new closed sample record"""
	data = _read()
	closed_sample_id = data["next_id"]
	
	# Calculate corrected weight (weight - moisture weight)
	moisture_weight = weight * (moisture / 100) if moisture > 0 else 0
	corrected_weight = weight - moisture_weight
	
	closed_sample = {
		"id": closed_sample_id,
		"closing_date": closing_date,
		"customer_name": customer_name,
		"sample_name": sample_name,
		"encoding": encoding,
		"box_symbol": box_symbol,
		"weight": weight,
		"moisture": moisture,
		"corrected_weight": corrected_weight,
		"note": note,
		"created_at": datetime.now().isoformat()
	}
	
	data["closed_samples"].append(closed_sample)
	data["next_id"] += 1
	_write(data)
	
	return closed_sample_id


def create_closed_sample_with_boxes(
	closing_date: str,
	customer_name: str,
	sample_name: str,
	encoding: str,
	boxes: List[Dict[str, Any]],
	note: str = ""
) -> List[int]:
	"""Create multiple closed sample records for the same sample with different boxes"""
	data = _read()
	created_ids = []
	
	for box in boxes:
		closed_sample_id = data["next_id"]
		
		# Calculate corrected weight (weight - moisture weight)
		weight = float(box.get("weight", 0))
		moisture = float(box.get("moisture", 0))
		moisture_weight = weight * (moisture / 100) if moisture > 0 else 0
		corrected_weight = weight - moisture_weight
		
		closed_sample = {
			"id": closed_sample_id,
			"closing_date": closing_date,
			"customer_name": customer_name,
			"sample_name": sample_name,
			"encoding": encoding,
			"box_symbol": box.get("box_symbol", ""),
			"weight": weight,
			"moisture": moisture,
			"corrected_weight": corrected_weight,
			"note": note,
			"created_at": datetime.now().isoformat()
		}
		
		data["closed_samples"].append(closed_sample)
		data["next_id"] += 1
		created_ids.append(closed_sample_id)
	
	_write(data)
	return created_ids


def get_closed_sample(closed_sample_id: int) -> Optional[Dict[str, Any]]:
	"""Get a specific closed sample by ID"""
	closed_samples = list_closed_samples()
	for sample in closed_samples:
		if sample["id"] == closed_sample_id:
			return sample
	return None


def update_closed_sample(
	closed_sample_id: int,
	closing_date: str,
	customer_name: str,
	sample_name: str,
	encoding: str,
	box_symbol: str,
	weight: float,
	moisture: float,
	note: str = ""
) -> bool:
	"""Update an existing closed sample"""
	data = _read()
	for sample in data["closed_samples"]:
		if sample["id"] == closed_sample_id:
			# Calculate corrected weight
			moisture_weight = weight * (moisture / 100) if moisture > 0 else 0
			corrected_weight = weight - moisture_weight
			
			sample["closing_date"] = closing_date
			sample["customer_name"] = customer_name
			sample["sample_name"] = sample_name
			sample["encoding"] = encoding
			sample["box_symbol"] = box_symbol
			sample["weight"] = weight
			sample["moisture"] = moisture
			sample["corrected_weight"] = corrected_weight
			sample["note"] = note
			
			_write(data)
			return True
	return False


def delete_closed_sample(closed_sample_id: int) -> bool:
	"""Delete a closed sample"""
	data = _read()
	data["closed_samples"] = [s for s in data["closed_samples"] if s["id"] != closed_sample_id]
	_write(data)
	return True


def export_closed_samples_to_excel() -> str:
	"""Export closed samples to Excel format"""
	import io
	import pandas as pd
	
	closed_samples = list_closed_samples()
	
	# Create DataFrame
	df = pd.DataFrame(closed_samples)
	
	# Reorder columns for better display
	column_order = [
		"id", "closing_date", "customer_name", "sample_name", "encoding", 
		"box_symbol", "weight", "moisture", "corrected_weight", "note"
	]
	
	# Only include columns that exist in the data
	available_columns = [col for col in column_order if col in df.columns]
	df = df[available_columns]
	
	# Rename columns to Vietnamese
	column_names = {
		"id": "ID",
		"closing_date": "Ngày đóng mẫu",
		"customer_name": "Tên khách hàng",
		"sample_name": "Tên mẫu",
		"encoding": "Mã hóa",
		"box_symbol": "Ký hiệu box",
		"weight": "Khối lượng cân (g)",
		"moisture": "Độ ẩm (%)",
		"corrected_weight": "Khối lượng hiệu chỉnh (g)",
		"note": "Ghi chú"
	}
	
	df = df.rename(columns=column_names)
	
	# Create Excel file in memory
	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Mẫu đã đóng', index=False)
	
	output.seek(0)
	return output.getvalue()


def validate_sample_exists(customer_name: str, sample_name: str, encoding: str) -> tuple[bool, str]:
	"""Validate if sample exists in the samples module. Returns (is_valid, error_message)"""
	from .samples_store import list_samples
	from .customers_store import list_customers
	
	# Get all samples and customers
	all_samples = list_samples()
	all_customers = list_customers()
	
	# Find customer by name
	customer = None
	for c in all_customers:
		if c.get("name", "").lower() == customer_name.lower():
			customer = c
			break
	
	if not customer:
		return False, f"Không tìm thấy khách hàng '{customer_name}' trong module Nhận mẫu"
	
	customer_id = customer.get("id")
	
	# Find sample by customer_id, sample_name, and sample_code
	for sample in all_samples:
		if (sample.get("customer_id") == customer_id and 
			sample.get("sample_name", "").lower() == sample_name.lower() and
			sample.get("sample_code", "").lower() == encoding.lower()):
			return True, ""
	
	return False, f"Không tìm thấy mẫu '{sample_name}' với mã hóa '{encoding}' của khách hàng '{customer_name}' trong module Nhận mẫu"


def import_closed_samples_from_csv(csv_content: str) -> tuple[int, List[str]]:
	"""Import closed samples from CSV content. Returns (success_count, error_messages)"""
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
			'Ngày đóng mẫu': 'closing_date',
			'Tên khách hàng': 'customer_name',
			'Tên mẫu': 'sample_name',
			'Mã hóa': 'encoding',
			'Ký hiệu box': 'box_symbol',
			'Khối lượng cân (g)': 'weight',
			'Độ ẩm (%)': 'moisture',
			'Khối lượng hiệu chỉnh (g)': 'corrected_weight',
			'Ghi chú': 'note'
		}
		
		# Map Vietnamese headers to English field names
		mapped_header = []
		for col in header:
			mapped_header.append(field_mapping.get(col, col))
		
		# Debug: Check if mapping worked
		required_fields = ['closing_date', 'customer_name', 'sample_name', 'encoding', 'box_symbol', 'weight']
		for field in required_fields:
			if field not in mapped_header:
				# Map back to Vietnamese for error message
				vi_names = {
					'closing_date': 'Ngày đóng mẫu',
					'customer_name': 'Tên khách hàng',
					'sample_name': 'Tên mẫu',
					'encoding': 'Mã hóa',
					'box_symbol': 'Ký hiệu box',
					'weight': 'Khối lượng cân (g)'
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
			if not row.get('closing_date') or not row.get('customer_name') or not row.get('sample_name'):
				errors.append(f"Dòng {i}: Thiếu thông tin bắt buộc")
				continue
			
			try:
				# Parse weight and moisture
				weight = float(row.get('weight', 0))
				moisture = float(row.get('moisture', 0))
				
				# Validate sample exists in samples module
				is_valid, error_msg = validate_sample_exists(
					row['customer_name'],
					row['sample_name'],
					row.get('encoding', '')
				)
				
				if not is_valid:
					errors.append(f"Dòng {i}: {error_msg}")
					continue
				
				# Create closed sample
				create_closed_sample(
					closing_date=row['closing_date'],
					customer_name=row['customer_name'],
					sample_name=row['sample_name'],
					encoding=row.get('encoding', ''),
					box_symbol=row.get('box_symbol', ''),
					weight=weight,
					moisture=moisture,
					note=row.get('note', '')
				)
				success_count += 1
			except Exception as e:
				errors.append(f"Dòng {i}: Lỗi tạo mẫu đóng - {str(e)}")
				
	except Exception as e:
		errors.append(f"Lỗi đọc file CSV: {str(e)}")
	
	return success_count, errors
