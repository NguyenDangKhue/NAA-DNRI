import json
import os
import io
import csv
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(CUSTOMERS_FILE):
		with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
			json.dump({"next_id": 1, "customers": []}, f, ensure_ascii=False, indent=2)


def _read() -> Dict[str, Any]:
	_ensure_store()
	with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
		return json.load(f)


def _write(data: Dict[str, Any]) -> None:
	with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def list_customers() -> List[Dict[str, Any]]:
	return _read().get("customers", [])


def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
	for c in list_customers():
		if c.get("id") == customer_id:
			return c
	return None


def create_customer(name: str, organization: str, phone: str, address: str, note: str) -> int:
	data = _read()
	customer_id = data.get("next_id", 1)
	record = {
		"id": customer_id,
		"name": name.strip(),
		"organization": organization.strip(),
		"phone": phone.strip(),
		"address": address.strip(),
		"note": note.strip(),
	}
	data.setdefault("customers", []).append(record)
	data["next_id"] = customer_id + 1
	_write(data)
	return customer_id


def update_customer(customer_id: int, name: str, organization: str, phone: str, address: str, note: str) -> bool:
	data = _read()
	found = False
	for c in data.get("customers", []):
		if c.get("id") == customer_id:
			c["name"] = name.strip()
			c["organization"] = organization.strip()
			c["phone"] = phone.strip()
			c["address"] = address.strip()
			c["note"] = note.strip()
			found = True
			break
	if not found:
		return False
	_write(data)
	return True


def delete_customer(customer_id: int) -> bool:
	data = _read()
	customers = data.get("customers", [])
	new_customers = [c for c in customers if c.get("id") != customer_id]
	if len(new_customers) == len(customers):
		return False
	data["customers"] = new_customers
	_write(data)
	return True


def export_customers_to_excel() -> str:
	"""Export customers data to CSV format (Excel compatible)"""
	customers = list_customers()
	
	# Create CSV content
	output = io.StringIO()
	writer = csv.writer(output)
	
	# Write header
	writer.writerow(['ID', 'Tên khách hàng', 'Đơn vị trực thuộc', 'Số điện thoại', 'Địa chỉ', 'Ghi chú'])
	
	# Write data
	for customer in customers:
		writer.writerow([
			customer.get('id', ''),
			customer.get('name', ''),
			customer.get('organization', ''),
			customer.get('phone', ''),
			customer.get('address', ''),
			customer.get('note', '')
		])
	
	return output.getvalue()
