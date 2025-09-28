import json
import os
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SAMPLES_FILE = os.path.join(DATA_DIR, "samples.json")


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(SAMPLES_FILE):
		with open(SAMPLES_FILE, "w", encoding="utf-8") as f:
			json.dump({"next_id": 1, "samples": []}, f, ensure_ascii=False, indent=2)


def _read() -> Dict[str, Any]:
	_ensure_store()
	with open(SAMPLES_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _write(data: Dict[str, Any]) -> None:
	with open(SAMPLES_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def list_samples() -> List[Dict[str, Any]]:
	return _read().get("samples", [])


def list_samples_paginated(page: int = 1, per_page: int = 20, customer_id: Optional[int] = None) -> tuple[List[Dict[str, Any]], int, int]:
	"""Get paginated samples with optional customer filter. Returns (samples, total_pages, total_count)"""
	all_samples = _read().get("samples", [])
	
	# Filter by customer if specified
	if customer_id is not None:
		all_samples = [s for s in all_samples if s.get("customer_id") == customer_id]
	
	total_count = len(all_samples)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Calculate offset
	offset = (page - 1) * per_page
	
	# Get samples for current page
	samples = all_samples[offset:offset + per_page]
	
	return samples, total_pages, total_count


def get_sample(sample_id: int) -> Optional[Dict[str, Any]]:
	for s in list_samples():
		if s.get("id") == sample_id:
			return s
	return None


def create_sample(customer_id: int, sample_name: str, sample_code: str, sample_type: str, analysis_target: str, note: str) -> int:
	data = _read()
	samples = data.get("samples", [])
	
	# Validate uniqueness within the same customer
	sample_name = sample_name.strip()
	sample_code = sample_code.strip()
	
	# Check for duplicate sample name within the same customer
	for existing_sample in samples:
		if (existing_sample.get("customer_id") == customer_id and 
			existing_sample.get("sample_name", "").strip().lower() == sample_name.lower()):
			raise ValueError(f"Tên mẫu '{sample_name}' đã tồn tại cho khách hàng này")
	
	# Check for duplicate sample code within the same customer
	for existing_sample in samples:
		if (existing_sample.get("customer_id") == customer_id and 
			existing_sample.get("sample_code", "").strip().lower() == sample_code.lower() and
			sample_code):  # Only check if sample_code is not empty
			raise ValueError(f"Mã hóa mẫu '{sample_code}' đã tồn tại cho khách hàng này")
	
	# ID is always the next sequential number (1, 2, 3, 4...)
	sample_id = len(samples) + 1
	
	record = {
		"id": sample_id,
		"received_date": datetime.now().strftime("%Y-%m-%d"),
		"customer_id": customer_id,
		"sample_name": sample_name,
		"sample_code": sample_code,
		"sample_type": sample_type.strip(),
		"analysis_target": analysis_target.strip(),
		"note": note.strip(),
	}
	samples.append(record)
	data["samples"] = samples
	_write(data)
	return sample_id


def update_sample(sample_id: int, customer_id: int, sample_name: str, sample_code: str, sample_type: str, analysis_target: str, note: str) -> bool:
	data = _read()
	found = False
	
	# Validate uniqueness within the same customer (excluding current sample)
	sample_name = sample_name.strip()
	sample_code = sample_code.strip()
	
	# Check for duplicate sample name within the same customer (excluding current sample)
	for existing_sample in data.get("samples", []):
		if (existing_sample.get("id") != sample_id and
			existing_sample.get("customer_id") == customer_id and 
			existing_sample.get("sample_name", "").strip().lower() == sample_name.lower()):
			raise ValueError(f"Tên mẫu '{sample_name}' đã tồn tại cho khách hàng này")
	
	# Check for duplicate sample code within the same customer (excluding current sample)
	for existing_sample in data.get("samples", []):
		if (existing_sample.get("id") != sample_id and
			existing_sample.get("customer_id") == customer_id and 
			existing_sample.get("sample_code", "").strip().lower() == sample_code.lower() and
			sample_code):  # Only check if sample_code is not empty
			raise ValueError(f"Mã hóa mẫu '{sample_code}' đã tồn tại cho khách hàng này")
	
	for s in data.get("samples", []):
		if s.get("id") == sample_id:
			s["customer_id"] = customer_id
			s["sample_name"] = sample_name
			s["sample_code"] = sample_code
			s["sample_type"] = sample_type.strip()
			s["analysis_target"] = analysis_target.strip()
			s["note"] = note.strip()
			found = True
			break
	if not found:
		return False
	_write(data)
	return True


def delete_sample(sample_id: int) -> bool:
	data = _read()
	samples = data.get("samples", [])
	
	# Find and remove the sample
	original_count = len(samples)
	new_samples = [s for s in samples if s.get("id") != sample_id]
	
	if len(new_samples) == original_count:
		return False  # Sample not found
	
	# Renumber all samples to maintain sequential IDs (1, 2, 3, 4...)
	for i, sample in enumerate(new_samples, 1):
		sample["id"] = i
	
	data["samples"] = new_samples
	_write(data)
	return True


def import_samples_from_csv(csv_content: str) -> tuple[int, List[str]]:
	"""Import samples from CSV content. Returns (success_count, error_messages)"""
	errors = []
	success_count = 0
	
	try:
		# Use proper CSV parsing with StringIO
		import io
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
			'ID Khách hàng': 'customer_id',
			'Tên mẫu': 'sample_name', 
			'Mã hóa mẫu': 'sample_code',
			'Loại mẫu': 'sample_type',
			'Chỉ tiêu phân tích': 'analysis_target',
			'Ghi chú': 'note'
		}
		
		# Map Vietnamese headers to English field names
		mapped_header = []
		for col in header:
			mapped_header.append(field_mapping.get(col, col))
		
		# Debug: Check if mapping worked
		if 'customer_id' not in mapped_header or 'sample_name' not in mapped_header:
			errors.append(f"Header không đúng. Cần có: 'ID Khách hàng' và 'Tên mẫu'. Nhận được: {header}")
			return 0, errors
		
		required_fields = ['customer_id', 'sample_name']
		
		# Validate header
		for field in required_fields:
			if field not in mapped_header:
				# Map back to Vietnamese for error message
				vi_names = {
					'customer_id': 'ID Khách hàng',
					'sample_name': 'Tên mẫu'
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
			if not row.get('customer_id') or not row.get('sample_name'):
				errors.append(f"Dòng {i}: Thiếu thông tin bắt buộc")
				continue
			
			try:
				customer_id = int(row['customer_id'])
			except ValueError:
				errors.append(f"Dòng {i}: customer_id phải là số")
				continue
			
			# Create sample
			try:
				create_sample(
					customer_id=customer_id,
					sample_name=row['sample_name'],
					sample_code=row.get('sample_code', ''),
					sample_type=row.get('sample_type', ''),
					analysis_target=row.get('analysis_target', ''),
					note=row.get('note', '')
				)
				success_count += 1
			except Exception as e:
				errors.append(f"Dòng {i}: Lỗi tạo mẫu - {str(e)}")
				
	except Exception as e:
		errors.append(f"Lỗi đọc file CSV: {str(e)}")
	
	return success_count, errors


def export_samples_to_excel(customer_id: Optional[int] = None) -> str:
	"""Export samples to Excel format. Returns CSV content for Excel."""
	all_samples = _read().get("samples", [])
	print(f"DEBUG: Total samples: {len(all_samples)}")
	print(f"DEBUG: Filtering by customer_id: {customer_id}")
	
	# Filter by customer if specified
	if customer_id is not None:
		all_samples = [s for s in all_samples if s.get("customer_id") == customer_id]
		print(f"DEBUG: Filtered samples: {len(all_samples)}")
	
	# Create CSV content
	import io
	output = io.StringIO()
	writer = csv.writer(output)
	
	# Write header
	writer.writerow(['ID', 'Ngày nhận', 'ID Khách hàng', 'Tên mẫu', 'Mã hóa mẫu', 'Loại mẫu', 'Chỉ tiêu phân tích', 'Ghi chú'])
	
	# Write data
	for sample in all_samples:
		writer.writerow([
			sample.get('id', ''),
			sample.get('received_date', ''),
			sample.get('customer_id', ''),
			sample.get('sample_name', ''),
			sample.get('sample_code', ''),
			sample.get('sample_type', ''),
			sample.get('analysis_target', ''),
			sample.get('note', '')
		])
	
	return output.getvalue()


def save_filtered_samples_to_temp(customer_id: Optional[int] = None) -> str:
	"""Save filtered samples to temporary file. Returns temp file path."""
	import tempfile
	import os
	
	all_samples = _read().get("samples", [])
	
	# Filter by customer if specified
	if customer_id is not None:
		all_samples = [s for s in all_samples if s.get("customer_id") == customer_id]
	
	# Create temporary file
	temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
	os.makedirs(temp_dir, exist_ok=True)
	
	# Create temp file with unique name
	import uuid
	temp_filename = f"filtered_samples_{uuid.uuid4().hex}.json"
	temp_path = os.path.join(temp_dir, temp_filename)
	
	# Save filtered samples to temp file with metadata
	temp_data = {
		"customer_id": customer_id,
		"samples": all_samples,
		"count": len(all_samples)
	}
	
	with open(temp_path, 'w', encoding='utf-8') as f:
		json.dump(temp_data, f, ensure_ascii=False, indent=2)
	
	print(f"DEBUG: Saved {len(all_samples)} filtered samples to {temp_path}")
	return temp_path


def load_filtered_samples_from_temp(temp_path: str) -> tuple[List[Dict[str, Any]], Optional[int]]:
	"""Load filtered samples from temporary file. Returns (samples, customer_id)."""
	try:
		with open(temp_path, 'r', encoding='utf-8') as f:
			temp_data = json.load(f)
		
		# Handle both old format (list) and new format (dict)
		if isinstance(temp_data, list):
			samples = temp_data
			customer_id = None
		else:
			samples = temp_data.get("samples", [])
			customer_id = temp_data.get("customer_id")
		
		print(f"DEBUG: Loaded {len(samples)} samples from temp file, customer_id: {customer_id}")
		return samples, customer_id
	except Exception as e:
		print(f"DEBUG: Error loading temp file: {e}")
		return [], None


def cleanup_temp_file(temp_path: str) -> None:
	"""Clean up temporary file."""
	try:
		if os.path.exists(temp_path):
			os.remove(temp_path)
			print(f"DEBUG: Cleaned up temp file: {temp_path}")
	except Exception as e:
		print(f"DEBUG: Error cleaning up temp file: {e}")
