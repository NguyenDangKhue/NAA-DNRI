import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DATA_FILE = "data/channel_7_1_irradiations.json"

def load_channel_7_1_irradiations() -> List[Dict]:
	"""Load channel 7-1 irradiations from JSON file"""
	if not os.path.exists(DATA_FILE):
		return []
	
	try:
		with open(DATA_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			return data.get('irradiations', [])
	except (json.JSONDecodeError, FileNotFoundError):
		return []

def save_channel_7_1_irradiations(irradiations: List[Dict]) -> None:
	"""Save channel 7-1 irradiations to JSON file"""
	os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
	
	data = {
		'irradiations': irradiations,
		'last_updated': datetime.now().isoformat()
	}
	
	with open(DATA_FILE, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)

def list_channel_7_1_irradiations() -> List[Dict]:
	"""Get all channel 7-1 irradiations"""
	return load_channel_7_1_irradiations()

def list_channel_7_1_irradiations_paginated(page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int, int]:
	"""Get paginated channel 7-1 irradiations"""
	irradiations = load_channel_7_1_irradiations()
	
	# Calculate pagination
	total_count = len(irradiations)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Get page data
	start_idx = (page - 1) * per_page
	end_idx = start_idx + per_page
	page_irradiations = irradiations[start_idx:end_idx]
	
	return page_irradiations, total_pages, total_count

def create_channel_7_1_irradiation(sample_code: str, sample_name: str, channel_position: str, 
								  irradiation_time: float, power: float, temperature: float = None, 
								  note: str = "") -> Dict:
	"""Create a new channel 7-1 irradiation"""
	irradiations = load_channel_7_1_irradiations()
	
	# Generate new ID
	next_id = max([i.get('id', 0) for i in irradiations], default=0) + 1
	
	irradiation = {
		'id': next_id,
		'sample_code': sample_code,
		'sample_name': sample_name,
		'channel_position': channel_position,
		'irradiation_time': irradiation_time,
		'power': power,
		'temperature': temperature,
		'note': note,
		'created_at': datetime.now().isoformat()
	}
	
	irradiations.append(irradiation)
	save_channel_7_1_irradiations(irradiations)
	
	return irradiation

def get_channel_7_1_irradiation(irradiation_id: int) -> Optional[Dict]:
	"""Get a specific channel 7-1 irradiation by ID"""
	irradiations = load_channel_7_1_irradiations()
	
	for irradiation in irradiations:
		if irradiation.get('id') == irradiation_id:
			return irradiation
	
	return None

def update_channel_7_1_irradiation(irradiation_id: int, sample_code: str, sample_name: str, 
								   channel_position: str, irradiation_time: float, power: float, 
								   temperature: float = None, note: str = "") -> bool:
	"""Update a channel 7-1 irradiation"""
	irradiations = load_channel_7_1_irradiations()
	
	for i, irradiation in enumerate(irradiations):
		if irradiation.get('id') == irradiation_id:
			irradiations[i].update({
				'sample_code': sample_code,
				'sample_name': sample_name,
				'channel_position': channel_position,
				'irradiation_time': irradiation_time,
				'power': power,
				'temperature': temperature,
				'note': note,
				'updated_at': datetime.now().isoformat()
			})
			save_channel_7_1_irradiations(irradiations)
			return True
	
	return False

def delete_channel_7_1_irradiation(irradiation_id: int) -> bool:
	"""Delete a channel 7-1 irradiation"""
	irradiations = load_channel_7_1_irradiations()
	
	for i, irradiation in enumerate(irradiations):
		if irradiation.get('id') == irradiation_id:
			del irradiations[i]
			save_channel_7_1_irradiations(irradiations)
			return True
	
	return False

def export_channel_7_1_irradiations_to_excel() -> str:
	"""Export channel 7-1 irradiations to Excel format"""
	import io
	from openpyxl import Workbook
	
	irradiations = load_channel_7_1_irradiations()
	
	wb = Workbook()
	ws = wb.active
	ws.title = "Chiếu mẫu kênh 7-1"
	
	# Headers
	headers = ['ID', 'Mã mẫu', 'Tên mẫu', 'Vị trí kênh', 'Thời gian chiếu (phút)', 
			  'Công suất (kW)', 'Nhiệt độ (°C)', 'Ghi chú', 'Ngày tạo']
	ws.append(headers)
	
	# Data
	for irradiation in irradiations:
		row = [
			irradiation.get('id', ''),
			irradiation.get('sample_code', ''),
			irradiation.get('sample_name', ''),
			irradiation.get('channel_position', ''),
			irradiation.get('irradiation_time', ''),
			irradiation.get('power', ''),
			irradiation.get('temperature', ''),
			irradiation.get('note', ''),
			irradiation.get('created_at', '')
		]
		ws.append(row)
	
	# Save to bytes
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)
	
	return output.getvalue()
