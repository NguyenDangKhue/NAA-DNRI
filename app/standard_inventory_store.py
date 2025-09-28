import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from werkzeug.utils import secure_filename

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
INVENTORIES_FILE = os.path.join(DATA_DIR, "standard_inventories.json")
CERTIFICATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "certificates")

# Ensure certificates directory exists
os.makedirs(CERTIFICATES_DIR, exist_ok=True)


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(INVENTORIES_FILE):
		with open(INVENTORIES_FILE, "w", encoding="utf-8") as f:
			json.dump({"next_id": 1, "inventories": []}, f, ensure_ascii=False, indent=2)


def _read() -> Dict[str, Any]:
	_ensure_store()
	with open(INVENTORIES_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _write(data: Dict[str, Any]) -> None:
	with open(INVENTORIES_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def list_inventories() -> List[Dict[str, Any]]:
	"""Get all standard inventories with calculated used weight from standards"""
	from app.standard_store import list_standards
	
	data = _read()
	inventories = data.get("inventories", [])
	
	# Get all standards to calculate used weight
	standards = list_standards()
	
	# Calculate used weight for each inventory
	for inventory in inventories:
		standard_name = inventory.get("standard_name", "")
		used_weight = 0
		
		# Sum up weight from standards with matching standard_name
		for standard in standards:
			if standard.get("standard_name") == standard_name:
				used_weight += standard.get("weight", 0)
		
		# Update used weight and calculate remaining weight
		inventory["used_weight"] = used_weight
		total_weight = inventory.get("total_weight", 0)
		inventory["remaining_weight"] = total_weight - used_weight
	
	return inventories


def list_inventories_paginated(page: int = 1, per_page: int = 20, standard_type: Optional[str] = None) -> tuple[List[Dict[str, Any]], int, int]:
	"""Get paginated inventories with optional type filter. Returns (inventories, total_pages, total_count)"""
	from app.standard_store import list_standards
	
	all_inventories = _read().get("inventories", [])
	
	# Filter by standard type if specified
	if standard_type:
		all_inventories = [i for i in all_inventories if i.get("standard_type", "").lower() == standard_type.lower()]
	
	total_count = len(all_inventories)
	total_pages = (total_count + per_page - 1) // per_page
	
	# Calculate offset
	offset = (page - 1) * per_page
	
	# Get inventories for current page
	inventories = all_inventories[offset:offset + per_page]
	
	# Get all standards to calculate used weight
	standards = list_standards()
	
	# Calculate used weight for each inventory
	for inventory in inventories:
		standard_name = inventory.get("standard_name", "")
		used_weight = 0
		
		# Sum up weight from standards with matching standard_name
		for standard in standards:
			if standard.get("standard_name") == standard_name:
				used_weight += standard.get("weight", 0)
		
		# Update used weight and calculate remaining weight
		inventory["used_weight"] = used_weight
		total_weight = inventory.get("total_weight", 0)
		inventory["remaining_weight"] = total_weight - used_weight
	
	return inventories, total_pages, total_count


def create_inventory(
	standard_name: str,
	box_symbol: str,
	total_weight: float,
	standard_type: str = "",
	certificate_file: Optional[str] = None,
	note: str = ""
) -> int:
	"""Create a new standard inventory record"""
	data = _read()
	inventory_id = data["next_id"]
	
	# Calculate used weight from standards
	from app.standard_store import list_standards
	standards = list_standards()
	used_weight = 0
	
	# Sum up weight from standards with matching standard_name
	for standard in standards:
		if standard.get("standard_name") == standard_name:
			used_weight += standard.get("weight", 0)
	
	# Calculate remaining weight
	remaining_weight = total_weight - used_weight
	
	inventory = {
		"id": inventory_id,
		"standard_name": standard_name,
		"box_symbol": box_symbol,
		"total_weight": total_weight,
		"used_weight": used_weight,
		"remaining_weight": remaining_weight,
		"standard_type": standard_type,
		"certificate_file": certificate_file,
		"note": note,
		"created_at": datetime.now().isoformat(),
		"updated_at": datetime.now().isoformat()
	}
	
	data["inventories"].append(inventory)
	data["next_id"] += 1
	_write(data)
	
	return inventory_id


def get_inventory(inventory_id: int) -> Optional[Dict[str, Any]]:
	"""Get a specific inventory by ID"""
	inventories = list_inventories()
	for inventory in inventories:
		if inventory["id"] == inventory_id:
			return inventory
	return None


def update_inventory(
	inventory_id: int,
	standard_name: str,
	box_symbol: str,
	total_weight: float,
	standard_type: str = "",
	note: str = ""
) -> bool:
	"""Update an existing inventory"""
	data = _read()
	for inventory in data["inventories"]:
		if inventory["id"] == inventory_id:
			# Calculate used weight from standards
			from app.standard_store import list_standards
			standards = list_standards()
			used_weight = 0
			
			# Sum up weight from standards with matching standard_name
			for standard in standards:
				if standard.get("standard_name") == standard_name:
					used_weight += standard.get("weight", 0)
			
			# Calculate remaining weight
			remaining_weight = total_weight - used_weight
			
			inventory["standard_name"] = standard_name
			inventory["box_symbol"] = box_symbol
			inventory["total_weight"] = total_weight
			inventory["used_weight"] = used_weight
			inventory["remaining_weight"] = remaining_weight
			inventory["standard_type"] = standard_type
			inventory["note"] = note
			inventory["updated_at"] = datetime.now().isoformat()
			
			_write(data)
			return True
	return False


def update_used_weight(inventory_id: int, used_weight: float) -> bool:
	"""Update used weight and recalculate remaining weight"""
	data = _read()
	for inventory in data["inventories"]:
		if inventory["id"] == inventory_id:
			total_weight = inventory["total_weight"]
			remaining_weight = total_weight - used_weight
			
			inventory["used_weight"] = used_weight
			inventory["remaining_weight"] = remaining_weight
			inventory["updated_at"] = datetime.now().isoformat()
			
			_write(data)
			return True
	return False


def delete_inventory(inventory_id: int) -> bool:
	"""Delete an inventory and its certificate file"""
	data = _read()
	for inventory in data["inventories"]:
		if inventory["id"] == inventory_id:
			# Delete certificate file if exists
			if inventory.get("certificate_file"):
				certificate_path = os.path.join(CERTIFICATES_DIR, inventory["certificate_file"])
				if os.path.exists(certificate_path):
					os.remove(certificate_path)
			
			data["inventories"] = [i for i in data["inventories"] if i["id"] != inventory_id]
			_write(data)
			return True
	return False


def upload_certificate(inventory_id: int, file) -> bool:
	"""Upload certificate file for an inventory"""
	if not file or not file.filename:
		return False
	
	# Check if file is PDF
	if not file.filename.lower().endswith('.pdf'):
		return False
	
	# Secure filename
	filename = secure_filename(file.filename)
	# Add timestamp to avoid conflicts
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	filename = f"{inventory_id}_{timestamp}_{filename}"
	
	# Save file
	file_path = os.path.join(CERTIFICATES_DIR, filename)
	file.save(file_path)
	
	# Update inventory record
	data = _read()
	for inventory in data["inventories"]:
		if inventory["id"] == inventory_id:
			# Delete old certificate if exists
			if inventory.get("certificate_file"):
				old_certificate_path = os.path.join(CERTIFICATES_DIR, inventory["certificate_file"])
				if os.path.exists(old_certificate_path):
					os.remove(old_certificate_path)
			
			inventory["certificate_file"] = filename
			inventory["updated_at"] = datetime.now().isoformat()
			_write(data)
			return True
	return False


def get_certificate_path(inventory_id: int) -> Optional[str]:
	"""Get certificate file path for an inventory"""
	inventory = get_inventory(inventory_id)
	if not inventory or not inventory.get("certificate_file"):
		return None
	
	certificate_path = os.path.join(CERTIFICATES_DIR, inventory["certificate_file"])
	if os.path.exists(certificate_path):
		return certificate_path
	return None


def export_inventories_to_excel() -> str:
	"""Export inventories to Excel format"""
	import io
	import pandas as pd
	
	inventories = list_inventories()
	
	# Create DataFrame
	df = pd.DataFrame(inventories)
	
	# Reorder columns for better display
	column_order = [
		"id", "standard_name", "box_symbol", "total_weight", "used_weight", 
		"remaining_weight", "standard_type", "note", "created_at"
	]
	
	# Only include columns that exist in the data
	available_columns = [col for col in column_order if col in df.columns]
	df = df[available_columns]
	
	# Rename columns to Vietnamese
	column_names = {
		"id": "ID",
		"standard_name": "Tên mẫu chuẩn",
		"box_symbol": "Ký hiệu box",
		"total_weight": "Khối lượng tổng (g)",
		"used_weight": "Khối lượng đã sử dụng (g)",
		"remaining_weight": "Khối lượng còn lại (g)",
		"standard_type": "Loại mẫu chuẩn",
		"note": "Ghi chú",
		"created_at": "Ngày tạo"
	}
	
	# Convert standard_type values to Vietnamese for display
	def convert_standard_type(value):
		if value == "thuc_vat":
			return "Mẫu chuẩn thực vật"
		elif value == "dat_da":
			return "Mẫu chuẩn đất đá"
		return value
	
	# Apply conversion to standard_type column if it exists
	if "standard_type" in df.columns:
		df["standard_type"] = df["standard_type"].apply(convert_standard_type)
	
	df = df.rename(columns=column_names)
	
	# Create Excel file in memory
	output = io.BytesIO()
	with pd.ExcelWriter(output, engine='openpyxl') as writer:
		df.to_excel(writer, sheet_name='Danh sách mẫu chuẩn', index=False)
	
	output.seek(0)
	return output.getvalue()
