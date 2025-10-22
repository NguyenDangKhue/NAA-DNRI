import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ROTATING_DISK_FILE = os.path.join(DATA_DIR, "rotating_disk_irradiations.json")


def _ensure_store() -> None:
	"""Ensure the data directory and file exist"""
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(ROTATING_DISK_FILE):
		with open(ROTATING_DISK_FILE, 'w', encoding='utf-8') as f:
			json.dump({"batches": []}, f, ensure_ascii=False, indent=2)


def load_rotating_disk_irradiations() -> List[Dict]:
	"""Load all rotating disk irradiations from file"""
	_ensure_store()
	try:
		with open(ROTATING_DISK_FILE, 'r', encoding='utf-8') as f:
			data = json.load(f)
			return data.get("batches", [])
	except (FileNotFoundError, json.JSONDecodeError):
		return []


def save_rotating_disk_irradiations(batches: List[Dict]) -> None:
	"""Save rotating disk irradiations to file"""
	_ensure_store()
	with open(ROTATING_DISK_FILE, 'w', encoding='utf-8') as f:
		json.dump({"batches": batches}, f, ensure_ascii=False, indent=2)


def list_rotating_disk_irradiations_paginated(page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int, int]:
	"""Get paginated list of rotating disk irradiation batches"""
	batches = load_rotating_disk_irradiations()
	total_count = len(batches)
	total_pages = (total_count + per_page - 1) // per_page
	
	start_idx = (page - 1) * per_page
	end_idx = start_idx + per_page
	page_batches = batches[start_idx:end_idx]
	
	return page_batches, total_pages, total_count


def create_rotating_disk_batch(start_time: str, irradiation_time: float, power: float, 
							  samples: List[Dict], batch_note: str = "") -> Dict:
	"""Create a new rotating disk irradiation batch"""
	batches = load_rotating_disk_irradiations()
	
	# Generate new batch ID
	next_batch_id = max([b.get('batch_id', 0) for b in batches], default=0) + 1
	
	# Calculate end time
	start_dt = datetime.fromisoformat(start_time.replace('T', ' '))
	end_dt = datetime.fromtimestamp(start_dt.timestamp() + (irradiation_time * 60))
	
	batch = {
		'batch_id': next_batch_id,
		'start_time': start_time,
		'end_time': end_dt.isoformat(),
		'irradiation_time': irradiation_time,
		'power': power,
		'batch_note': batch_note,
		'samples': samples,
		'sample_count': len(samples),
		'created_at': datetime.now().isoformat()
	}
	
	batches.append(batch)
	save_rotating_disk_irradiations(batches)
	
	return batch


def get_rotating_disk_batch(batch_id: int) -> Optional[Dict]:
	"""Get a specific rotating disk irradiation batch by ID"""
	batches = load_rotating_disk_irradiations()
	for batch in batches:
		if batch.get('batch_id') == batch_id:
			return batch
	return None


def update_rotating_disk_batch(batch_id: int, **kwargs) -> bool:
	"""Update a rotating disk irradiation batch"""
	batches = load_rotating_disk_irradiations()
	for batch in batches:
		if batch.get('batch_id') == batch_id:
			batch.update(kwargs)
			batch['updated_at'] = datetime.now().isoformat()
			save_rotating_disk_irradiations(batches)
			return True
	return False


def delete_rotating_disk_batch(batch_id: int) -> bool:
	"""Delete a rotating disk irradiation batch"""
	batches = load_rotating_disk_irradiations()
	batches = [b for b in batches if b.get('batch_id') != batch_id]
	save_rotating_disk_irradiations(batches)
	return True


def export_rotating_disk_irradiations_to_excel() -> str:
	"""Export rotating disk irradiations to Excel file"""
	import pandas as pd
	from io import BytesIO
	import base64
	
	batches = load_rotating_disk_irradiations()
	
	# Flatten data for Excel export
	export_data = []
	for batch in batches:
		for sample in batch.get('samples', []):
			export_data.append({
				'Batch ID': batch.get('batch_id'),
				'Thời gian bắt đầu': batch.get('start_time', '')[:16],
				'Thời gian kết thúc': batch.get('end_time', '')[:16],
				'Thời gian chiếu (phút)': batch.get('irradiation_time'),
				'Công suất (kW)': batch.get('power'),
				'Ghi chú lần chiếu': batch.get('batch_note', ''),
				'Mã mẫu': sample.get('sample_code'),
				'Tên mẫu': sample.get('sample_name'),
				'Vị trí mâm quay': sample.get('disk_position'),
				'Ngày tạo': batch.get('created_at', '')[:16]
			})
	
	if not export_data:
		export_data = [{'Thông báo': 'Chưa có dữ liệu'}]
	
	df = pd.DataFrame(export_data)
	
	# Create Excel file in memory
	output = BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Chiếu mẫu mâm quay', index=False)
	
	output.seek(0)
	excel_data = base64.b64encode(output.getvalue()).decode()
	
	return excel_data


# Legacy functions for backward compatibility
def create_rotating_disk_irradiation(sample_code: str, sample_name: str, disk_position: int, 
									irradiation_time: float, power: float, note: str = "") -> Dict:
	"""Legacy function - Create a single sample irradiation (converted to batch)"""
	now = datetime.now().isoformat()
	samples = [{
		'sample_code': sample_code,
		'sample_name': sample_name,
		'disk_position': disk_position,
		'note': note
	}]
	
	return create_rotating_disk_batch(
		start_time=now,
		irradiation_time=irradiation_time,
		power=power,
		samples=samples,
		batch_note=note
	)


def get_rotating_disk_irradiation(irradiation_id: int) -> Optional[Dict]:
	"""Legacy function - Get single irradiation (now returns batch)"""
	return get_rotating_disk_batch(irradiation_id)