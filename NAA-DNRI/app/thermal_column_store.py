import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DATA_FILE = "data/thermal_column_irradiations.json"

def load_thermal_column_irradiations() -> List[Dict]:
	"""Load thermal column irradiations from JSON file"""
	if not os.path.exists(DATA_FILE):
		return []
	
	try:
		with open(DATA_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			return data.get('irradiations', [])
	except (json.JSONDecodeError, FileNotFoundError):
		return []

def save_thermal_column_irradiations(irradiations: List[Dict]) -> None:
	"""Save thermal column irradiations to JSON file"""
	os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
	
	data = {
		'irradiations': irradiations,
		'last_updated': datetime.now().isoformat()
	}
	
	with open(DATA_FILE, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

def list_thermal_column_irradiations() -> List[Dict]:
	"""Get all thermal column irradiations"""
	return load_thermal_column_irradiations()

def list_thermal_column_irradiations_paginated(page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int, int]:
	"""Get paginated thermal column irradiations"""
	irradiations = load_thermal_column_irradiations()
	
	# Calculate pagination
	total_count = len(irradiations)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Get page data
	start_idx = (page - 1) * per_page
	end_idx = start_idx + per_page
	page_irradiations = irradiations[start_idx:end_idx]
	
	return page_irradiations, total_pages, total_count

def create_thermal_column_irradiation(sample_code: str, sample_name: str, irradiation_type: str, 
									position: str, irradiation_time: float, power: float, 
									temperature: float = None, pressure: float = None, 
									note: str = "") -> Dict:
	"""Create a new thermal column irradiation"""
	irradiations = load_thermal_column_irradiations()
	
	# Generate new ID
	next_id = max([i.get('id', 0) for i in irradiations], default=0) + 1
	
	irradiation = {
		'id': next_id,
		'sample_code': sample_code,
		'sample_name': sample_name,
		'irradiation_type': irradiation_type,
		'position': position,
		'irradiation_time': irradiation_time,
		'power': power,
		'temperature': temperature,
		'pressure': pressure,
		'note': note,
		'created_at': datetime.now().isoformat()
	}
	
	irradiations.append(irradiation)
	save_thermal_column_irradiations(irradiations)
	
	return irradiation

def get_thermal_column_irradiation(irradiation_id: int) -> Optional[Dict]:
	"""Get a specific thermal column irradiation by ID"""
	irradiations = load_thermal_column_irradiations()
	
	for irradiation in irradiations:
		if irradiation.get('id') == irradiation_id:
			return irradiation
	
	return None

def update_thermal_column_irradiation(irradiation_id: int, sample_code: str, sample_name: str, 
									  irradiation_type: str, position: str, irradiation_time: float, 
									  power: float, temperature: float = None, pressure: float = None, 
									  note: str = "") -> bool:
	"""Update a thermal column irradiation"""
	irradiations = load_thermal_column_irradiations()
	
	for i, irradiation in enumerate(irradiations):
		if irradiation.get('id') == irradiation_id:
			irradiations[i].update({
				'sample_code': sample_code,
				'sample_name': sample_name,
				'irradiation_type': irradiation_type,
				'position': position,
				'irradiation_time': irradiation_time,
				'power': power,
				'temperature': temperature,
				'pressure': pressure,
				'note': note,
				'updated_at': datetime.now().isoformat()
			})
			save_thermal_column_irradiations(irradiations)
			return True
	
	return False

def delete_thermal_column_irradiation(irradiation_id: int) -> bool:
	"""Delete a thermal column irradiation"""
	irradiations = load_thermal_column_irradiations()
	
	for i, irradiation in enumerate(irradiations):
		if irradiation.get('id') == irradiation_id:
			del irradiations[i]
			save_thermal_column_irradiations(irradiations)
			return True
	
	return False

def export_thermal_column_irradiations_to_excel() -> str:
	"""Export thermal column irradiations to Excel format"""
	import io
	from openpyxl import Workbook
	
	irradiations = load_thermal_column_irradiations()
	
	wb = Workbook()
	ws = wb.active
	ws.title = "Chiếu mẫu cột nhiệt và 13-2"
	
	# Headers
	headers = ['ID', 'Mã mẫu', 'Tên mẫu', 'Loại chiếu', 'Vị trí', 'Thời gian chiếu (phút)', 
			  'Công suất (kW)', 'Nhiệt độ (°C)', 'Áp suất (bar)', 'Ghi chú', 'Ngày tạo']
	ws.append(headers)
	
	# Data
	for irradiation in irradiations:
		row = [
			irradiation.get('id', ''),
			irradiation.get('sample_code', ''),
			irradiation.get('sample_name', ''),
			irradiation.get('irradiation_type', ''),
			irradiation.get('position', ''),
			irradiation.get('irradiation_time', ''),
			irradiation.get('power', ''),
			irradiation.get('temperature', ''),
			irradiation.get('pressure', ''),
			irradiation.get('note', ''),
			irradiation.get('created_at', '')
		]
		ws.append(row)
	
	# Save to bytes
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)
	
	return output.getvalue()
