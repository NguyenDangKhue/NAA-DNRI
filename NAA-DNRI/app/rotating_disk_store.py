import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DATA_FILE = "data/rotating_disk_irradiations.json"

def load_rotating_disk_irradiations() -> List[Dict]:
	"""Load rotating disk irradiations from JSON file"""
	if not os.path.exists(DATA_FILE):
		return []
	
	try:
		with open(DATA_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			return data.get('irradiations', [])
	except (json.JSONDecodeError, FileNotFoundError):
		return []

def save_rotating_disk_irradiations(irradiations: List[Dict]) -> None:
	"""Save rotating disk irradiations to JSON file"""
	os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
	
	data = {
		'irradiations': irradiations,
		'last_updated': datetime.now().isoformat()
	}
	
	with open(DATA_FILE, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

def list_rotating_disk_irradiations() -> List[Dict]:
	"""Get all rotating disk irradiations"""
	return load_rotating_disk_irradiations()

def list_rotating_disk_irradiations_paginated(page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int, int]:
	"""Get paginated rotating disk irradiations"""
	irradiations = load_rotating_disk_irradiations()
	
	# Calculate pagination
	total_count = len(irradiations)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Get page data
	start_idx = (page - 1) * per_page
	end_idx = start_idx + per_page
	page_irradiations = irradiations[start_idx:end_idx]
	
	return page_irradiations, total_pages, total_count

def create_rotating_disk_irradiation(sample_code: str, sample_name: str, disk_position: int, 
									irradiation_time: float, power: float, note: str = "") -> Dict:
	"""Create a new rotating disk irradiation"""
	irradiations = load_rotating_disk_irradiations()
	
	# Generate new ID
	next_id = max([i.get('id', 0) for i in irradiations], default=0) + 1
	
	irradiation = {
		'id': next_id,
		'sample_code': sample_code,
		'sample_name': sample_name,
		'disk_position': disk_position,
		'irradiation_time': irradiation_time,
		'power': power,
		'note': note,
		'created_at': datetime.now().isoformat()
	}
	
	irradiations.append(irradiation)
	save_rotating_disk_irradiations(irradiations)
	
	return irradiation

def get_rotating_disk_irradiation(irradiation_id: int) -> Optional[Dict]:
	"""Get a specific rotating disk irradiation by ID"""
	irradiations = load_rotating_disk_irradiations()
	
	for irradiation in irradiations:
		if irradiation.get('id') == irradiation_id:
			return irradiation
	
	return None

def update_rotating_disk_irradiation(irradiation_id: int, sample_code: str, sample_name: str, 
								   disk_position: int, irradiation_time: float, power: float, 
								   note: str = "") -> bool:
	"""Update a rotating disk irradiation"""
	irradiations = load_rotating_disk_irradiations()
	
	for i, irradiation in enumerate(irradiations):
		if irradiation.get('id') == irradiation_id:
			irradiations[i].update({
				'sample_code': sample_code,
				'sample_name': sample_name,
				'disk_position': disk_position,
				'irradiation_time': irradiation_time,
				'power': power,
				'note': note,
				'updated_at': datetime.now().isoformat()
			})
			save_rotating_disk_irradiations(irradiations)
			return True
	
	return False

def delete_rotating_disk_irradiation(irradiation_id: int) -> bool:
	"""Delete a rotating disk irradiation"""
	irradiations = load_rotating_disk_irradiations()
	
	for i, irradiation in enumerate(irradiations):
		if irradiation.get('id') == irradiation_id:
			del irradiations[i]
			save_rotating_disk_irradiations(irradiations)
			return True
	
	return False

def export_rotating_disk_irradiations_to_excel() -> str:
	"""Export rotating disk irradiations to Excel format"""
	import io
	from openpyxl import Workbook
	
	irradiations = load_rotating_disk_irradiations()
	
	wb = Workbook()
	ws = wb.active
	ws.title = "Chiếu mẫu mâm quay"
	
	# Headers
	headers = ['ID', 'Mã mẫu', 'Tên mẫu', 'Vị trí mâm quay', 'Thời gian chiếu (phút)', 
			  'Công suất (kW)', 'Ghi chú', 'Ngày tạo']
	ws.append(headers)
	
	# Data
	for irradiation in irradiations:
		row = [
			irradiation.get('id', ''),
			irradiation.get('sample_code', ''),
			irradiation.get('sample_name', ''),
			irradiation.get('disk_position', ''),
			irradiation.get('irradiation_time', ''),
			irradiation.get('power', ''),
			irradiation.get('note', ''),
			irradiation.get('created_at', '')
		]
		ws.append(row)
	
	# Save to bytes
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)
	
	return output.getvalue()
