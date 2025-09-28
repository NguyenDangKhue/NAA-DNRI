from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from .auth import login_required, verify_credentials, admin_required, permission_required
from .users_store import load_users, create_user, delete_user, DEFAULT_SECTIONS
from .customers_store import list_customers, create_customer, delete_customer, get_customer, update_customer, export_customers_to_excel
from .samples_store import list_samples, list_samples_paginated, create_sample, delete_sample, get_sample, update_sample, import_samples_from_csv, export_samples_to_excel, save_filtered_samples_to_temp, load_filtered_samples_from_temp, cleanup_temp_file
from .closed_samples_store import list_closed_samples, list_closed_samples_paginated, create_closed_sample, delete_closed_sample, export_closed_samples_to_excel, import_closed_samples_from_csv
from .foil_store import list_foils, list_foils_paginated, create_foil, delete_foil, get_foil, update_foil, export_foils_to_excel, import_foils_from_csv
from .standard_store import list_standards, list_standards_paginated, create_standard, delete_standard, get_standard, update_standard, export_standards_to_excel, import_standards_from_csv
from .standard_inventory_store import list_inventories, list_inventories_paginated, create_inventory, delete_inventory, get_inventory, update_inventory, upload_certificate, get_certificate_path, export_inventories_to_excel


pages = Blueprint("pages", __name__)


@pages.route("/", methods=["GET"])
@login_required
def index():
	sections = [
		("Quản lý người dùng", "/users"),
		("Quản lý khách hàng", "/customers"),
		("Nhận mẫu", "/receiving"),
		("Đóng mẫu", "/closing"),
		("Chiếu mẫu", "/irradiation"),
	]
	return render_template("home.html", sections=sections, username=session.get("username"))


@pages.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")
		if verify_credentials(username, password):
			session["user_id"] = username
			session["username"] = username
			return redirect(url_for("pages.index"))
		flash("Sai tên đăng nhập hoặc mật khẩu", "danger")
	return render_template("login.html")


@pages.route("/logout", methods=["GET"])
def logout():
	session.clear()
	return redirect(url_for("pages.login"))


# Users management (admin only)
@pages.route("/users", methods=["GET"]) 
@admin_required
def users_list():
	users = load_users()
	return render_template("users/list.html", users=users, default_sections=DEFAULT_SECTIONS)


@pages.route("/users/create", methods=["POST"]) 
@admin_required
def users_create():
	username = request.form.get("username", "").strip()
	password = request.form.get("password", "").strip()
	role = request.form.get("role", "user")
	permissions = request.form.getlist("permissions") or []
	if role == "admin":
		permissions = DEFAULT_SECTIONS
	if not username or not password:
		flash("Vui lòng nhập tên đăng nhập và mật khẩu", "warning")
		return redirect(url_for("pages.users_list"))
	if create_user(username, password, role, permissions):
		flash("Tạo người dùng thành công", "success")
	else:
		flash("Tên đăng nhập đã tồn tại hoặc không hợp lệ", "danger")
	return redirect(url_for("pages.users_list"))


@pages.route("/users/delete/<username>", methods=["POST"]) 
@admin_required
def users_delete(username: str):
	if delete_user(username):
		flash("Đã xoá người dùng", "success")
	else:
		flash("Không thể xoá người dùng này", "danger")
	return redirect(url_for("pages.users_list"))


# Customers management (permission: customers)
@pages.route("/customers", methods=["GET"]) 
@permission_required("customers")
def customers_list():
	customers = list_customers()
	return render_template("customers/list.html", customers=customers)


@pages.route("/customers/create", methods=["POST"]) 
@permission_required("customers")
def customers_create():
	name = request.form.get("name", "")
	organization = request.form.get("organization", "")
	phone = request.form.get("phone", "")
	address = request.form.get("address", "")
	note = request.form.get("note", "")
	if not name.strip():
		flash("Vui lòng nhập tên khách hàng", "warning")
		return redirect(url_for("pages.customers_list"))
	create_customer(name, organization, phone, address, note)
	flash("Đã thêm khách hàng", "success")
	return redirect(url_for("pages.customers_list"))


@pages.route("/customers/delete/<int:customer_id>", methods=["POST"]) 
@permission_required("customers")
def customers_delete(customer_id: int):
	if delete_customer(customer_id):
		flash("Đã xoá khách hàng", "success")
	else:
		flash("Không tìm thấy khách hàng", "danger")
	return redirect(url_for("pages.customers_list"))


@pages.route("/customers/<int:customer_id>/edit", methods=["GET"]) 
@permission_required("customers")
def customers_edit(customer_id: int):
	customer = get_customer(customer_id)
	if not customer:
		flash("Không tìm thấy khách hàng", "danger")
		return redirect(url_for("pages.customers_list"))
	return render_template("customers/edit.html", customer=customer)


@pages.route("/customers/<int:customer_id>/edit", methods=["POST"]) 
@permission_required("customers")
def customers_update(customer_id: int):
	name = request.form.get("name", "")
	organization = request.form.get("organization", "")
	phone = request.form.get("phone", "")
	address = request.form.get("address", "")
	note = request.form.get("note", "")
	if not name.strip():
		flash("Vui lòng nhập tên khách hàng", "warning")
		return redirect(url_for("pages.customers_edit", customer_id=customer_id))
	if update_customer(customer_id, name, organization, phone, address, note):
		flash("Đã cập nhật khách hàng", "success")
	else:
		flash("Cập nhật thất bại", "danger")
	return redirect(url_for("pages.customers_list"))


@pages.route("/customers/export")
@permission_required("customers")
def customers_export():
	"""Export customers to Excel format"""
	from flask import Response
	from urllib.parse import quote
	
	try:
		# Export customers to CSV format
		csv_content = export_customers_to_excel()
		
		# Create filename with timestamp
		from datetime import datetime
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"danh_sach_khach_hang_{timestamp}.csv"
		
		# Return with proper headers for Excel compatibility
		response = Response(
			csv_content.encode('utf-8-sig'),  # Add BOM for Excel compatibility
			mimetype='text/csv; charset=utf-8',
			headers={
				'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{quote(filename)}',
				'Content-Type': 'text/csv; charset=utf-8',
				'Cache-Control': 'no-cache'
			}
		)
		return response
		
	except Exception as e:
		flash(f"Lỗi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.customers_list"))


# Samples management (permission: receiving)
@pages.route("/receiving", methods=["GET"]) 
@permission_required("receiving")
def samples_list():
	# Get pagination and filter parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	customer_id = request.args.get('customer_id', '')
	
	# Convert customer_id to int if provided
	customer_id = int(customer_id) if customer_id and customer_id.isdigit() else None
	
	# Get paginated samples
	samples, total_pages, total_count = list_samples_paginated(page, per_page, customer_id)
	customers = list_customers()
	
	# Create customer lookup for display
	customer_lookup = {c["id"]: c["name"] for c in customers}
	
	return render_template("samples/list.html", 
		samples=samples, 
		customers=customers, 
		customer_lookup=customer_lookup,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_customer_id=customer_id
	)


@pages.route("/receiving/create", methods=["POST"]) 
@permission_required("receiving")
def samples_create():
	customer_id = request.form.get("customer_id", "")
	sample_name = request.form.get("sample_name", "")
	sample_code = request.form.get("sample_code", "")
	sample_type = request.form.get("sample_type", "")
	analysis_target = request.form.get("analysis_target", "")
	note = request.form.get("note", "")
	if not customer_id or not sample_name.strip():
		flash("Vui lòng chọn khách hàng và nhập tên mẫu", "warning")
		return redirect(url_for("pages.samples_list"))
	
	try:
		create_sample(int(customer_id), sample_name, sample_code, sample_type, analysis_target, note)
		flash("Đã thêm mẫu", "success")
	except ValueError as e:
		flash(str(e), "danger")
	except Exception as e:
		flash(f"Lỗi khi thêm mẫu: {str(e)}", "danger")
	
	return redirect(url_for("pages.samples_list"))


@pages.route("/receiving/delete/<int:sample_id>", methods=["POST"]) 
@permission_required("receiving")
def samples_delete(sample_id: int):
	if delete_sample(sample_id):
		flash("Đã xoá mẫu", "success")
	else:
		flash("Không tìm thấy mẫu", "danger")
	return redirect(url_for("pages.samples_list"))


@pages.route("/receiving/<int:sample_id>/edit", methods=["GET"]) 
@permission_required("receiving")
def samples_edit(sample_id: int):
	sample = get_sample(sample_id)
	if not sample:
		flash("Không tìm thấy mẫu", "danger")
		return redirect(url_for("pages.samples_list"))
	customers = list_customers()
	return render_template("samples/edit.html", sample=sample, customers=customers)


@pages.route("/receiving/<int:sample_id>/edit", methods=["POST"]) 
@permission_required("receiving")
def samples_update(sample_id: int):
	customer_id = request.form.get("customer_id", "")
	sample_name = request.form.get("sample_name", "")
	sample_code = request.form.get("sample_code", "")
	sample_type = request.form.get("sample_type", "")
	analysis_target = request.form.get("analysis_target", "")
	note = request.form.get("note", "")
	if not customer_id or not sample_name.strip():
		flash("Vui lòng chọn khách hàng và nhập tên mẫu", "warning")
		return redirect(url_for("pages.samples_edit", sample_id=sample_id))
	
	try:
		if update_sample(sample_id, int(customer_id), sample_name, sample_code, sample_type, analysis_target, note):
			flash("Đã cập nhật mẫu", "success")
		else:
			flash("Cập nhật thất bại", "danger")
	except ValueError as e:
		flash(str(e), "danger")
	except Exception as e:
		flash(f"Lỗi khi cập nhật mẫu: {str(e)}", "danger")
	
	return redirect(url_for("pages.samples_list"))


@pages.route("/receiving/import", methods=["POST"]) 
@permission_required("receiving")
def samples_import():
	if 'csv_file' not in request.files:
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.samples_list"))
	
	file = request.files['csv_file']
	if file.filename == '':
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.samples_list"))
	
	if not file.filename.lower().endswith('.csv'):
		flash("File phải có định dạng CSV", "danger")
		return redirect(url_for("pages.samples_list"))
	
	try:
		# Try different encodings for Vietnamese
		try:
			csv_content = file.read().decode('utf-8-sig')
		except UnicodeDecodeError:
			try:
				csv_content = file.read().decode('utf-8')
			except UnicodeDecodeError:
				csv_content = file.read().decode('cp1252')
		
		success_count, errors = import_samples_from_csv(csv_content)
		
		if success_count > 0:
			flash(f"Đã import thành công {success_count} mẫu", "success")
		
		if errors:
			for error in errors:
				flash(error, "warning")
				
	except Exception as e:
		flash(f"Lỗi đọc file: {str(e)}", "danger")
	
	return redirect(url_for("pages.samples_list"))


@pages.route("/receiving/template")
@permission_required("receiving")
def samples_template():
	from flask import Response, request
	import os
	
	# Get customer_id from query parameter
	customer_id = request.args.get('customer_id', '')
	
	# Read the CSV template file with proper encoding
	template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "templates")
	file_path = os.path.join(template_path, "samples_template.csv")
	
	# Read with UTF-8 encoding
	with open(file_path, 'r', encoding='utf-8') as f:
		content = f.read()
	
	# If customer_id is provided, replace the customer ID in the template
	if customer_id and customer_id.isdigit():
		lines = content.split('\n')
		# Update data rows to use the selected customer ID
		for i in range(1, len(lines)):
			if lines[i].strip():  # Skip empty lines
				parts = lines[i].split(',')
				if len(parts) >= 6:  # Ensure we have enough columns
					parts[0] = customer_id  # Replace first column (customer ID)
					lines[i] = ','.join(parts)
		content = '\n'.join(lines)
	
	# Return with proper headers to avoid Excel warnings
	response = Response(
		content.encode('utf-8-sig'),  # Add BOM for Excel compatibility
		mimetype='text/csv; charset=utf-8',
		headers={
			'Content-Disposition': 'attachment; filename=samples_template.csv',
			'Content-Type': 'text/csv; charset=utf-8',
			'Cache-Control': 'no-cache'
		}
	)
	return response


@pages.route("/receiving/export")
@permission_required("receiving")
def samples_export():
	from flask import Response
	
	# Get filter parameters
	customer_id = request.args.get('customer_id', '')
	print(f"DEBUG: Received customer_id: {customer_id}")
	print(f"DEBUG: Request args: {dict(request.args)}")
	customer_id = int(customer_id) if customer_id and customer_id.isdigit() else None
	print(f"DEBUG: Parsed customer_id: {customer_id}")
	
	# Export samples to Excel format
	try:
		csv_content = export_samples_to_excel(customer_id)
		print(f"DEBUG: CSV content length: {len(csv_content)}")
		print(f"DEBUG: CSV content preview: {csv_content[:200]}...")
	except Exception as e:
		print(f"DEBUG: Error in export_samples_to_excel: {e}")
		flash(f"Lỗi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.samples_list"))
	
	# Determine filename - sanitize for safe download
	if customer_id:
		customers = list_customers()
		customer_lookup = {c["id"]: c["name"] for c in customers}
		customer_name = customer_lookup.get(customer_id, f"KhachHang_{customer_id}")
		
		# Sanitize customer name for filename
		import re
		safe_name = re.sub(r'[^\w\-_\.]', '_', customer_name)
		safe_name = safe_name.replace(' ', '_')
		# Limit filename length to avoid issues
		if len(safe_name) > 50:
			safe_name = safe_name[:50]
		filename = f"mau_khach_hang_{safe_name}.csv"
	else:
		filename = "tat_ca_mau.csv"
	
	print(f"DEBUG: Filename: {filename}")
	
	# Return with proper headers
	from urllib.parse import quote
	response = Response(
		csv_content.encode('utf-8-sig'),  # Add BOM for Excel compatibility
		mimetype='text/csv; charset=utf-8',
		headers={
			'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{quote(filename)}',
			'Content-Type': 'text/csv; charset=utf-8',
			'Cache-Control': 'no-cache'
		}
	)
	return response


@pages.route("/receiving/save-filtered")
@permission_required("receiving")
def samples_save_filtered():
	"""Save filtered samples to temporary file and return temp file ID."""
	try:
		customer_id = request.args.get('customer_id', '')
		customer_id = int(customer_id) if customer_id and customer_id.isdigit() else None
		
		print(f"DEBUG: Saving filtered samples for customer_id: {customer_id}")
		
		# Save filtered samples to temp file
		temp_path = save_filtered_samples_to_temp(customer_id)
		
		# Return temp file ID (just the filename)
		import os
		temp_filename = os.path.basename(temp_path)
		
		return jsonify({"temp_file": temp_filename, "message": "Dữ liệu đã lọc đã được lưu"})
		
	except Exception as e:
		print(f"DEBUG: Error in save-filtered: {e}")
		return jsonify({"error": str(e)}), 500


@pages.route("/receiving/export-from-temp/<temp_filename>")
@permission_required("receiving")
def samples_export_from_temp(temp_filename):
	"""Export samples from temporary file."""
	from flask import Response
	import os
	
	# Construct temp file path
	temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
	temp_path = os.path.join(temp_dir, temp_filename)
	
	print(f"DEBUG: Exporting from temp file: {temp_path}")
	
	try:
		# Load filtered samples from temp file
		filtered_samples, customer_id = load_filtered_samples_from_temp(temp_path)
		
		if not filtered_samples:
			flash("Không tìm thấy dữ liệu đã lọc", "danger")
			return redirect(url_for("pages.samples_list"))
		
		# Create CSV content
		import io
		import csv
		output = io.StringIO()
		writer = csv.writer(output)
		
		# Write header
		writer.writerow(['ID', 'Ngày nhận', 'ID Khách hàng', 'Tên mẫu', 'Mã hóa mẫu', 'Loại mẫu', 'Chỉ tiêu phân tích', 'Ghi chú'])
		
		# Write data
		for sample in filtered_samples:
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
		
		csv_content = output.getvalue()
		print(f"DEBUG: CSV content length: {len(csv_content)}")
		
		# Determine filename based on customer
		if customer_id:
			# Get customer name
			customers = list_customers()
			customer_lookup = {c["id"]: c["name"] for c in customers}
			customer_name = customer_lookup.get(customer_id, f"KhachHang_{customer_id}")
			
			# Strong sanitize customer name for filename
			import re
			# Remove all non-ASCII characters and replace with ASCII equivalents
			safe_name = customer_name
			# Replace Vietnamese characters
			safe_name = safe_name.replace('à', 'a').replace('á', 'a').replace('ạ', 'a').replace('ả', 'a').replace('ã', 'a')
			safe_name = safe_name.replace('â', 'a').replace('ầ', 'a').replace('ấ', 'a').replace('ậ', 'a').replace('ẩ', 'a').replace('ẫ', 'a')
			safe_name = safe_name.replace('ă', 'a').replace('ằ', 'a').replace('ắ', 'a').replace('ặ', 'a').replace('ẳ', 'a').replace('ẵ', 'a')
			safe_name = safe_name.replace('è', 'e').replace('é', 'e').replace('ẹ', 'e').replace('ẻ', 'e').replace('ẽ', 'e')
			safe_name = safe_name.replace('ê', 'e').replace('ề', 'e').replace('ế', 'e').replace('ệ', 'e').replace('ể', 'e').replace('ễ', 'e')
			safe_name = safe_name.replace('ì', 'i').replace('í', 'i').replace('ị', 'i').replace('ỉ', 'i').replace('ĩ', 'i')
			safe_name = safe_name.replace('ò', 'o').replace('ó', 'o').replace('ọ', 'o').replace('ỏ', 'o').replace('õ', 'o')
			safe_name = safe_name.replace('ô', 'o').replace('ồ', 'o').replace('ố', 'o').replace('ộ', 'o').replace('ổ', 'o').replace('ỗ', 'o')
			safe_name = safe_name.replace('ơ', 'o').replace('ờ', 'o').replace('ớ', 'o').replace('ợ', 'o').replace('ở', 'o').replace('ỡ', 'o')
			safe_name = safe_name.replace('ù', 'u').replace('ú', 'u').replace('ụ', 'u').replace('ủ', 'u').replace('ũ', 'u')
			safe_name = safe_name.replace('ư', 'u').replace('ừ', 'u').replace('ứ', 'u').replace('ự', 'u').replace('ử', 'u').replace('ữ', 'u')
			safe_name = safe_name.replace('ỳ', 'y').replace('ý', 'y').replace('ỵ', 'y').replace('ỷ', 'y').replace('ỹ', 'y')
			safe_name = safe_name.replace('đ', 'd').replace('Đ', 'D')
			
			# Remove all non-alphanumeric characters except underscore and hyphen
			safe_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', safe_name)
			# Replace multiple underscores with single underscore
			safe_name = re.sub(r'_+', '_', safe_name)
			# Remove leading/trailing underscores
			safe_name = safe_name.strip('_')
			# Limit filename length to avoid issues
			if len(safe_name) > 30:
				safe_name = safe_name[:30]
			# Ensure filename is not empty
			if not safe_name:
				safe_name = f"KhachHang_{customer_id}"
			
			# Ensure filename doesn't start with number or special character
			if safe_name and (safe_name[0].isdigit() or safe_name[0] in '._-'):
				safe_name = f"KhachHang_{safe_name}"
			
			filename = f"mau_khach_hang_{safe_name}.csv"
			print(f"DEBUG: Original name: {customer_name}, Safe name: {safe_name}, Filename: {filename}")
		else:
			filename = f"tat_ca_mau_{len(filtered_samples)}_mau.csv"
		
		# Return with proper headers
		from urllib.parse import quote
		response = Response(
			csv_content.encode('utf-8-sig'),
			mimetype='text/csv; charset=utf-8',
			headers={
				'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{quote(filename)}',
				'Content-Type': 'text/csv; charset=utf-8',
				'Cache-Control': 'no-cache'
			}
		)
		
		# Clean up temp file after successful export
		cleanup_temp_file(temp_path)
		
		return response
		
	except Exception as e:
		print(f"DEBUG: Error exporting from temp file: {e}")
		flash(f"Lỗi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.samples_list"))


# Sample Closing Module (permission: closing)
@pages.route("/closing", methods=["GET"]) 
@permission_required("closing")
def closing_index():
	"""Main closing module page with 3 sub-modules"""
	sub_modules = [
		("Đóng mẫu thường", "/closing/regular", "Quản lý số mẫu thường đã đóng"),
		("Đóng lá dò", "/closing/foil", "Quản lý số lá dò đã đóng"),
		("Đóng mẫu chuẩn", "/closing/standard", "Quản lý số mẫu chuẩn đã đóng")
	]
	return render_template("closing/index.html", sub_modules=sub_modules)


@pages.route("/closing/regular", methods=["GET"]) 
@permission_required("closing")
def closing_regular():
	"""Regular sample closing management"""
	# Get pagination and filter parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	customer_name = request.args.get('customer_name', '')
	
	# Get paginated closed samples
	closed_samples, total_pages, total_count = list_closed_samples_paginated(page, per_page, customer_name)
	
	# Get unique customer names for filter dropdown
	all_samples = list_closed_samples()
	unique_customers = list(set([s.get("customer_name", "") for s in all_samples if s.get("customer_name")]))
	unique_customers.sort()
	
	return render_template("closing/regular.html", 
		closed_samples=closed_samples,
		unique_customers=unique_customers,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_customer_name=customer_name
	)


@pages.route("/closing/regular/add", methods=["POST"])
@permission_required("closing")
def closing_regular_add():
	"""Add a new closed sample with multiple boxes"""
	try:
		closing_date = request.form.get("closing_date")
		customer_id = request.form.get("customer_id")
		customer_name = request.form.get("customer_name")
		sample_id = request.form.get("sample_id")
		sample_name = request.form.get("sample_name")
		encoding = request.form.get("encoding")
		note = request.form.get("note", "")
		
		# Validate required fields
		if not customer_id or not sample_id:
			flash("Vui lòng chọn khách hàng và mẫu", "warning")
			return redirect(url_for("pages.closing_regular"))
		
		# Parse boxes data from form
		boxes = []
		form_data = request.form.to_dict()
		
		# Extract box data from form
		box_indices = set()
		for key in form_data.keys():
			if key.startswith("boxes[") and "]" in key:
				# Extract index from key like "boxes[0][weight]"
				index = key.split("[")[1].split("]")[0]
				box_indices.add(index)
		
		# Process each box
		for box_index in box_indices:
			box_symbol = form_data.get(f"boxes[{box_index}][box_symbol]", "")
			weight = form_data.get(f"boxes[{box_index}][weight]", "0")
			moisture = form_data.get(f"boxes[{box_index}][moisture]", "0")
			
			if box_symbol and weight:  # Only add if box has required data
				boxes.append({
					"box_symbol": box_symbol,
					"weight": float(weight),
					"moisture": float(moisture)
				})
		
		if not boxes:
			flash("Vui lòng thêm ít nhất một box!", "danger")
			return redirect(url_for("pages.closing_regular"))
		
		# Get customer and sample info from database
		customer = get_customer(int(customer_id))
		sample = get_sample(int(sample_id))
		
		if not customer or not sample:
			flash("Không tìm thấy thông tin khách hàng hoặc mẫu", "danger")
			return redirect(url_for("pages.closing_regular"))
		
		# Use database info instead of form input
		actual_customer_name = customer.get("name", customer_name)
		actual_sample_name = sample.get("sample_name", sample_name)
		actual_sample_code = sample.get("sample_code", "")
		
		# Validate that the sample exists in the samples module
		from .closed_samples_store import validate_sample_exists
		is_valid, error_msg = validate_sample_exists(
			actual_customer_name,
			actual_sample_name,
			actual_sample_code
		)
		
		if not is_valid:
			flash(f"Lỗi validation: {error_msg}", "danger")
			return redirect(url_for("pages.closing_regular"))
		
		# Create closed samples with boxes
		from .closed_samples_store import create_closed_sample_with_boxes
		created_ids = create_closed_sample_with_boxes(
			closing_date=closing_date,
			customer_name=actual_customer_name,
			sample_name=actual_sample_name,
			encoding=encoding,
			boxes=boxes,
			note=note
		)
		
		flash(f"Đã thêm mẫu đóng thành công với {len(created_ids)} box!", "success")
		return redirect(url_for("pages.closing_regular"))
		
	except Exception as e:
		flash(f"Lỗi khi thêm mẫu đóng: {str(e)}", "danger")
		return redirect(url_for("pages.closing_regular"))


@pages.route("/closing/regular/edit/<int:closed_sample_id>", methods=["GET"])
@permission_required("closing")
def closing_regular_edit(closed_sample_id):
	"""Edit a closed sample - GET form"""
	from .closed_samples_store import get_closed_sample
	closed_sample = get_closed_sample(closed_sample_id)
	if not closed_sample:
		flash("Không tìm thấy mẫu đóng", "danger")
		return redirect(url_for("pages.closing_regular"))
	
	# Get unique customer names for dropdown
	all_samples = list_closed_samples()
	unique_customers = list(set([s.get("customer_name", "") for s in all_samples if s.get("customer_name")]))
	unique_customers.sort()
	
	return render_template("closing/edit_regular.html", 
		closed_sample=closed_sample,
		unique_customers=unique_customers
	)


@pages.route("/closing/regular/edit/<int:closed_sample_id>", methods=["POST"])
@permission_required("closing")
def closing_regular_update(closed_sample_id):
	"""Edit a closed sample - POST update"""
	try:
		closing_date = request.form.get("closing_date")
		customer_name = request.form.get("customer_name")
		sample_name = request.form.get("sample_name")
		encoding = request.form.get("encoding")
		box_symbol = request.form.get("box_symbol")
		weight = float(request.form.get("weight", 0))
		moisture = float(request.form.get("moisture", 0))
		note = request.form.get("note", "")
		
		# Validate required fields
		if not closing_date or not customer_name or not sample_name:
			flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.closing_regular_edit", closed_sample_id=closed_sample_id))
		
		# Validate that the sample exists in the samples module
		from .closed_samples_store import validate_sample_exists
		is_valid, error_msg = validate_sample_exists(
			customer_name,
			sample_name,
			encoding
		)
		
		if not is_valid:
			flash(f"Lỗi validation: {error_msg}", "danger")
			return redirect(url_for("pages.closing_regular_edit", closed_sample_id=closed_sample_id))
		
		# Update closed sample
		from .closed_samples_store import update_closed_sample
		if update_closed_sample(
			closed_sample_id=closed_sample_id,
			closing_date=closing_date,
			customer_name=customer_name,
			sample_name=sample_name,
			encoding=encoding,
			box_symbol=box_symbol,
			weight=weight,
			moisture=moisture,
			note=note
		):
			flash("Đã cập nhật mẫu đóng thành công!", "success")
		else:
			flash("Không tìm thấy mẫu đóng để cập nhật", "danger")
		
	except Exception as e:
		flash(f"Lỗi khi cập nhật mẫu đóng: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_regular"))


@pages.route("/closing/regular/delete/<int:closed_sample_id>", methods=["POST"])
@permission_required("closing")
def closing_regular_delete(closed_sample_id):
	"""Delete a closed sample"""
	try:
		delete_closed_sample(closed_sample_id)
		flash("Đã xóa mẫu đóng thành công!", "success")
	except Exception as e:
		flash(f"Lỗi khi xóa mẫu đóng: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_regular"))


@pages.route("/closing/regular/export")
@permission_required("closing")
def closing_regular_export():
	"""Export closed samples to Excel"""
	try:
		excel_data = export_closed_samples_to_excel()
		
		from flask import Response
		response = Response(
			excel_data,
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			headers={'Content-Disposition': 'attachment; filename=closed_samples.xlsx'}
		)
		return response
		
	except Exception as e:
		flash(f"Lỗi khi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.closing_regular"))


@pages.route("/closing/regular/template")
@permission_required("closing")
def closing_regular_template():
	"""Download CSV template for closed samples"""
	from flask import Response
	import os
	
	# Read the CSV template file with proper encoding
	template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "templates")
	file_path = os.path.join(template_path, "closed_samples_template.csv")
	
	# Read with UTF-8 encoding
	with open(file_path, 'r', encoding='utf-8') as f:
		content = f.read()
	
	# Return with proper headers to avoid Excel warnings
	response = Response(
		content.encode('utf-8-sig'),  # Add BOM for Excel compatibility
		mimetype='text/csv; charset=utf-8',
		headers={
			'Content-Disposition': 'attachment; filename=closed_samples_template.csv',
			'Content-Type': 'text/csv; charset=utf-8',
			'Cache-Control': 'no-cache'
		}
	)
	return response


@pages.route("/closing/regular/import", methods=["POST"])
@permission_required("closing")
def closing_regular_import():
	"""Import closed samples from CSV"""
	if 'csv_file' not in request.files:
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.closing_regular"))
	
	file = request.files['csv_file']
	if file.filename == '':
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.closing_regular"))
	
	if not file.filename.lower().endswith('.csv'):
		flash("File phải có định dạng CSV", "danger")
		return redirect(url_for("pages.closing_regular"))
	
	try:
		# Try different encodings for Vietnamese
		try:
			csv_content = file.read().decode('utf-8-sig')
		except UnicodeDecodeError:
			try:
				csv_content = file.read().decode('utf-8')
			except UnicodeDecodeError:
				csv_content = file.read().decode('cp1252')
		
		success_count, errors = import_closed_samples_from_csv(csv_content)
		
		if success_count > 0:
			flash(f"Đã import thành công {success_count} mẫu đóng", "success")
		
		if errors:
			for error in errors:
				flash(error, "warning")
				
	except Exception as e:
		flash(f"Lỗi đọc file: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_regular"))


@pages.route("/closing/foil", methods=["GET"]) 
@permission_required("closing")
def closing_foil():
	"""Foil sample closing management"""
	# Get pagination and filter parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	foil_type = request.args.get('foil_type', '')
	
	# Get paginated foils
	foils, total_pages, total_count = list_foils_paginated(page, per_page, foil_type)
	
	# Get unique foil types for filter dropdown
	all_foils = list_foils()
	unique_types = list(set([f.get("foil_type", "") for f in all_foils if f.get("foil_type")]))
	unique_types.sort()
	
	return render_template("closing/foil.html", 
		foils=foils,
		unique_types=unique_types,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_foil_type=foil_type
	)


@pages.route("/closing/foil/add", methods=["POST"])
@permission_required("closing")
def closing_foil_add():
	"""Add a new foil"""
	try:
		foil_code = request.form.get("foil_code", "").strip()
		foil_type = request.form.get("foil_type", "").strip()
		weight = float(request.form.get("weight", 0))
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not foil_code or not foil_type:
			flash("Vui lòng nhập mã lá dò và chọn loại lá dò", "warning")
			return redirect(url_for("pages.closing_foil"))
		
		# Create foil
		create_foil(
			foil_code=foil_code,
			foil_type=foil_type,
			weight=weight,
			note=note
		)
		
		flash("Đã thêm lá dò thành công!", "success")
		return redirect(url_for("pages.closing_foil"))
		
	except Exception as e:
		flash(f"Lỗi khi thêm lá dò: {str(e)}", "danger")
		return redirect(url_for("pages.closing_foil"))


@pages.route("/closing/foil/edit/<int:foil_id>", methods=["GET"])
@permission_required("closing")
def closing_foil_edit(foil_id):
	"""Edit a foil - GET form"""
	foil = get_foil(foil_id)
	if not foil:
		flash("Không tìm thấy lá dò", "danger")
		return redirect(url_for("pages.closing_foil"))
	
	# Get unique foil types for dropdown
	all_foils = list_foils()
	unique_types = list(set([f.get("foil_type", "") for f in all_foils if f.get("foil_type")]))
	unique_types.sort()
	
	return render_template("closing/edit_foil.html", 
		foil=foil,
		unique_types=unique_types
	)


@pages.route("/closing/foil/edit/<int:foil_id>", methods=["POST"])
@permission_required("closing")
def closing_foil_update(foil_id):
	"""Edit a foil - POST update"""
	try:
		foil_code = request.form.get("foil_code", "").strip()
		foil_type = request.form.get("foil_type", "").strip()
		weight = float(request.form.get("weight", 0))
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not foil_code or not foil_type:
			flash("Vui lòng nhập mã lá dò và chọn loại lá dò", "warning")
			return redirect(url_for("pages.closing_foil_edit", foil_id=foil_id))
		
		# Update foil
		if update_foil(
			foil_id=foil_id,
			foil_code=foil_code,
			foil_type=foil_type,
			weight=weight,
			note=note
		):
			flash("Đã cập nhật lá dò thành công!", "success")
		else:
			flash("Không tìm thấy lá dò để cập nhật", "danger")
		
	except Exception as e:
		flash(f"Lỗi khi cập nhật lá dò: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_foil"))


@pages.route("/closing/foil/delete/<int:foil_id>", methods=["POST"])
@permission_required("closing")
def closing_foil_delete(foil_id):
	"""Delete a foil"""
	try:
		delete_foil(foil_id)
		flash("Đã xóa lá dò thành công!", "success")
	except Exception as e:
		flash(f"Lỗi khi xóa lá dò: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_foil"))


@pages.route("/closing/foil/export")
@permission_required("closing")
def closing_foil_export():
	"""Export foils to Excel"""
	try:
		excel_data = export_foils_to_excel()
		
		from flask import Response
		response = Response(
			excel_data,
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			headers={'Content-Disposition': 'attachment; filename=foils.xlsx'}
		)
		return response
		
	except Exception as e:
		flash(f"Lỗi khi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.closing_foil"))


@pages.route("/closing/foil/template")
@permission_required("closing")
def closing_foil_template():
	"""Download CSV template for foils"""
	from flask import Response
	import os
	
	# Read the CSV template file with proper encoding
	template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "templates")
	file_path = os.path.join(template_path, "foil_template.csv")
	
	# Read with UTF-8 encoding
	with open(file_path, 'r', encoding='utf-8') as f:
		content = f.read()
	
	# Return with proper headers to avoid Excel warnings
	response = Response(
		content.encode('utf-8-sig'),  # Add BOM for Excel compatibility
		mimetype='text/csv; charset=utf-8',
		headers={
			'Content-Disposition': 'attachment; filename=foil_template.csv',
			'Content-Type': 'text/csv; charset=utf-8',
			'Cache-Control': 'no-cache'
		}
	)
	return response


@pages.route("/closing/foil/import", methods=["POST"])
@permission_required("closing")
def closing_foil_import():
	"""Import foils from CSV"""
	if 'csv_file' not in request.files:
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.closing_foil"))
	
	file = request.files['csv_file']
	if file.filename == '':
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.closing_foil"))
	
	if not file.filename.lower().endswith('.csv'):
		flash("File phải có định dạng CSV", "danger")
		return redirect(url_for("pages.closing_foil"))
	
	try:
		# Try different encodings for Vietnamese
		try:
			csv_content = file.read().decode('utf-8-sig')
		except UnicodeDecodeError:
			try:
				csv_content = file.read().decode('utf-8')
			except UnicodeDecodeError:
				csv_content = file.read().decode('cp1252')
		
		success_count, errors = import_foils_from_csv(csv_content)
		
		if success_count > 0:
			flash(f"Đã import thành công {success_count} lá dò", "success")
		
		if errors:
			for error in errors:
				flash(error, "warning")
				
	except Exception as e:
		flash(f"Lỗi đọc file: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_foil"))


@pages.route("/closing/standard", methods=["GET"]) 
@permission_required("closing")
def closing_standard():
	"""Standard sample closing management"""
	# Get pagination and filter parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	standard_type = request.args.get('standard_type', '')
	
	# Get paginated standards
	standards, total_pages, total_count = list_standards_paginated(page, per_page, standard_type)
	
	# Get unique standard types for filter dropdown
	all_standards = list_standards()
	unique_types = list(set([s.get("standard_type", "") for s in all_standards if s.get("standard_type")]))
	unique_types.sort()
	
	return render_template("closing/standard.html", 
		standards=standards,
		unique_types=unique_types,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_standard_type=standard_type
	)


@pages.route("/closing/standard/add", methods=["POST"])
@permission_required("closing")
def closing_standard_add():
	"""Add a new standard"""
	try:
		standard_name = request.form.get("standard_name", "").strip()
		box_name = request.form.get("box_name", "").strip()
		standard_type = request.form.get("standard_type", "").strip()
		weight = float(request.form.get("weight", 0))
		concentration = request.form.get("concentration", "").strip()
		moisture = float(request.form.get("moisture", 0))
		expiry_date = request.form.get("expiry_date", "").strip()
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not standard_name or not box_name or not standard_type:
			flash("Vui lòng nhập đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.closing_standard"))
		
		# Create standard
		create_standard(
			standard_name=standard_name,
			box_name=box_name,
			standard_type=standard_type,
			weight=weight,
			concentration=concentration,
			moisture=moisture,
			expiry_date=expiry_date,
			note=note
		)
		
		flash("Đã thêm mẫu chuẩn thành công!", "success")
		return redirect(url_for("pages.closing_standard"))
		
	except Exception as e:
		flash(f"Lỗi khi thêm mẫu chuẩn: {str(e)}", "danger")
		return redirect(url_for("pages.closing_standard"))


@pages.route("/closing/standard/edit/<int:standard_id>", methods=["GET"])
@permission_required("closing")
def closing_standard_edit(standard_id):
	"""Edit a standard - GET form"""
	standard = get_standard(standard_id)
	if not standard:
		flash("Không tìm thấy mẫu chuẩn", "danger")
		return redirect(url_for("pages.closing_standard"))
	
	# Get unique standard types for dropdown
	all_standards = list_standards()
	unique_types = list(set([s.get("standard_type", "") for s in all_standards if s.get("standard_type")]))
	unique_types.sort()
	
	return render_template("closing/edit_standard.html", 
		standard=standard,
		unique_types=unique_types
	)


@pages.route("/closing/standard/edit/<int:standard_id>", methods=["POST"])
@permission_required("closing")
def closing_standard_update(standard_id):
	"""Edit a standard - POST update"""
	try:
		standard_name = request.form.get("standard_name", "").strip()
		box_name = request.form.get("box_name", "").strip()
		standard_type = request.form.get("standard_type", "").strip()
		weight = float(request.form.get("weight", 0))
		concentration = request.form.get("concentration", "").strip()
		moisture = float(request.form.get("moisture", 0))
		expiry_date = request.form.get("expiry_date", "").strip()
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not standard_name or not box_name or not standard_type:
			flash("Vui lòng nhập đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.closing_standard_edit", standard_id=standard_id))
		
		# Update standard
		if update_standard(
			standard_id=standard_id,
			standard_name=standard_name,
			box_name=box_name,
			standard_type=standard_type,
			weight=weight,
			concentration=concentration,
			moisture=moisture,
			expiry_date=expiry_date,
			note=note
		):
			flash("Đã cập nhật mẫu chuẩn thành công!", "success")
		else:
			flash("Không tìm thấy mẫu chuẩn để cập nhật", "danger")
		
	except Exception as e:
		flash(f"Lỗi khi cập nhật mẫu chuẩn: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_standard"))


@pages.route("/closing/standard/delete/<int:standard_id>", methods=["POST"])
@permission_required("closing")
def closing_standard_delete(standard_id):
	"""Delete a standard"""
	try:
		delete_standard(standard_id)
		flash("Đã xóa mẫu chuẩn thành công!", "success")
	except Exception as e:
		flash(f"Lỗi khi xóa mẫu chuẩn: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_standard"))


@pages.route("/closing/standard/export")
@permission_required("closing")
def closing_standard_export():
	"""Export standards to Excel"""
	try:
		excel_data = export_standards_to_excel()
		
		from flask import Response
		response = Response(
			excel_data,
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			headers={'Content-Disposition': 'attachment; filename=standards.xlsx'}
		)
		return response
		
	except Exception as e:
		flash(f"Lỗi khi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.closing_standard"))


@pages.route("/closing/standard/template")
@permission_required("closing")
def closing_standard_template():
	"""Download CSV template for standards"""
	from flask import Response
	import os
	
	# Read the CSV template file with proper encoding
	template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "templates")
	file_path = os.path.join(template_path, "standard_template.csv")
	
	# Read with UTF-8 encoding
	with open(file_path, 'r', encoding='utf-8') as f:
		content = f.read()
	
	# Return with proper headers to avoid Excel warnings
	response = Response(
		content.encode('utf-8-sig'),  # Add BOM for Excel compatibility
		mimetype='text/csv; charset=utf-8',
		headers={
			'Content-Disposition': 'attachment; filename=standard_template.csv',
			'Content-Type': 'text/csv; charset=utf-8',
			'Cache-Control': 'no-cache'
		}
	)
	return response


@pages.route("/closing/standard/import", methods=["POST"])
@permission_required("closing")
def closing_standard_import():
	"""Import standards from CSV"""
	if 'csv_file' not in request.files:
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.closing_standard"))
	
	file = request.files['csv_file']
	if file.filename == '':
		flash("Vui lòng chọn file CSV", "warning")
		return redirect(url_for("pages.closing_standard"))
	
	if not file.filename.lower().endswith('.csv'):
		flash("File phải có định dạng CSV", "danger")
		return redirect(url_for("pages.closing_standard"))
	
	try:
		# Try different encodings for Vietnamese
		try:
			csv_content = file.read().decode('utf-8-sig')
		except UnicodeDecodeError:
			try:
				csv_content = file.read().decode('utf-8')
			except UnicodeDecodeError:
				csv_content = file.read().decode('cp1252')
		
		success_count, errors = import_standards_from_csv(csv_content)
		
		if success_count > 0:
			flash(f"Đã import thành công {success_count} mẫu chuẩn", "success")
		
		if errors:
			for error in errors:
				flash(error, "warning")
				
	except Exception as e:
		flash(f"Lỗi đọc file: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_standard"))


# Standard Inventory Management
@pages.route("/closing/standard/inventory", methods=["GET"]) 
@permission_required("closing")
def closing_standard_inventory():
	"""Standard inventory management"""
	# Get pagination and filter parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	standard_type = request.args.get('standard_type', '')
	
	# Get paginated inventories
	inventories, total_pages, total_count = list_inventories_paginated(page, per_page, standard_type)
	
	# Get unique standard types for filter dropdown
	all_inventories = list_inventories()
	unique_types = list(set([i.get("standard_type", "") for i in all_inventories if i.get("standard_type")]))
	unique_types.sort()
	
	return render_template("closing/standard_inventory.html", 
		inventories=inventories,
		unique_types=unique_types,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_standard_type=standard_type
	)


@pages.route("/closing/standard/inventory/add", methods=["POST"])
@permission_required("closing")
def closing_standard_inventory_add():
	"""Add a new standard to inventory"""
	try:
		standard_name = request.form.get("standard_name", "").strip()
		box_symbol = request.form.get("box_symbol", "").strip()
		total_weight = float(request.form.get("total_weight", 0))
		used_weight = float(request.form.get("used_weight", 0))
		standard_type = request.form.get("standard_type", "").strip()
		note = request.form.get("note", "").strip()
		
		# Handle certificate file upload
		certificate_file = None
		if 'certificate_file' in request.files:
			file = request.files['certificate_file']
			if file and file.filename:
				# Create inventory first to get ID
				inventory_id = create_inventory(
					standard_name=standard_name,
					box_symbol=box_symbol,
					total_weight=total_weight,
					used_weight=used_weight,
					standard_type=standard_type,
					note=note
				)
				
				# Upload certificate file
				if upload_certificate(inventory_id, file):
					flash("Đã thêm mẫu chuẩn vào kho thành công!", "success")
				else:
					flash("Đã thêm mẫu chuẩn nhưng lỗi upload file chứng nhận", "warning")
				return redirect(url_for("pages.closing_standard_inventory"))
		
		# Create inventory without certificate
		create_inventory(
			standard_name=standard_name,
			box_symbol=box_symbol,
			total_weight=total_weight,
			used_weight=used_weight,
			standard_type=standard_type,
			note=note
		)
		
		flash("Đã thêm mẫu chuẩn vào kho thành công!", "success")
		return redirect(url_for("pages.closing_standard_inventory"))
		
	except Exception as e:
		flash(f"Lỗi khi thêm mẫu chuẩn vào kho: {str(e)}", "danger")
		return redirect(url_for("pages.closing_standard_inventory"))


@pages.route("/closing/standard/inventory/edit/<int:inventory_id>", methods=["GET"])
@permission_required("closing")
def closing_standard_inventory_edit(inventory_id):
	"""Edit an inventory - GET form"""
	inventory = get_inventory(inventory_id)
	if not inventory:
		flash("Không tìm thấy mẫu chuẩn trong kho", "danger")
		return redirect(url_for("pages.closing_standard_inventory"))
	
	# Get unique standard types for dropdown
	all_inventories = list_inventories()
	unique_types = list(set([i.get("standard_type", "") for i in all_inventories if i.get("standard_type")]))
	unique_types.sort()
	
	return render_template("closing/edit_standard_inventory.html", 
		inventory=inventory,
		unique_types=unique_types
	)


@pages.route("/closing/standard/inventory/edit/<int:inventory_id>", methods=["POST"])
@permission_required("closing")
def closing_standard_inventory_update(inventory_id):
	"""Edit an inventory - POST update"""
	try:
		standard_name = request.form.get("standard_name", "").strip()
		box_symbol = request.form.get("box_symbol", "").strip()
		total_weight = float(request.form.get("total_weight", 0))
		used_weight = float(request.form.get("used_weight", 0))
		standard_type = request.form.get("standard_type", "").strip()
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not standard_name or not box_symbol:
			flash("Vui lòng nhập đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.closing_standard_inventory_edit", inventory_id=inventory_id))
		
		# Update inventory
		if update_inventory(
			inventory_id=inventory_id,
			standard_name=standard_name,
			box_symbol=box_symbol,
			total_weight=total_weight,
			used_weight=used_weight,
			standard_type=standard_type,
			note=note
		):
			flash("Đã cập nhật mẫu chuẩn thành công!", "success")
		else:
			flash("Không tìm thấy mẫu chuẩn để cập nhật", "danger")
		
	except Exception as e:
		flash(f"Lỗi khi cập nhật mẫu chuẩn: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_standard_inventory"))


@pages.route("/closing/standard/inventory/delete/<int:inventory_id>", methods=["POST"])
@permission_required("closing")
def closing_standard_inventory_delete(inventory_id):
	"""Delete an inventory"""
	try:
		delete_inventory(inventory_id)
		flash("Đã xóa mẫu chuẩn khỏi kho thành công!", "success")
	except Exception as e:
		flash(f"Lỗi khi xóa mẫu chuẩn: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_standard_inventory"))


@pages.route("/closing/standard/inventory/upload-certificate/<int:inventory_id>", methods=["POST"])
@permission_required("closing")
def closing_standard_inventory_upload_certificate(inventory_id):
	"""Upload certificate file for an inventory"""
	try:
		if 'certificate_file' not in request.files:
			flash("Vui lòng chọn file PDF", "warning")
			return redirect(url_for("pages.closing_standard_inventory"))
		
		file = request.files['certificate_file']
		if file.filename == '':
			flash("Vui lòng chọn file PDF", "warning")
			return redirect(url_for("pages.closing_standard_inventory"))
		
		if not file.filename.lower().endswith('.pdf'):
			flash("File phải có định dạng PDF", "danger")
			return redirect(url_for("pages.closing_standard_inventory"))
		
		if upload_certificate(inventory_id, file):
			flash("Đã upload file chứng nhận thành công!", "success")
		else:
			flash("Lỗi khi upload file chứng nhận", "danger")
		
	except Exception as e:
		flash(f"Lỗi khi upload file: {str(e)}", "danger")
	
	return redirect(url_for("pages.closing_standard_inventory"))


@pages.route("/closing/standard/inventory/download/<int:inventory_id>")
@permission_required("closing")
def closing_standard_inventory_download(inventory_id):
	"""Download certificate file for an inventory"""
	try:
		certificate_path = get_certificate_path(inventory_id)
		if not certificate_path:
			flash("Không tìm thấy file chứng nhận", "danger")
			return redirect(url_for("pages.closing_standard_inventory"))
		
		from flask import send_file
		return send_file(certificate_path, as_attachment=True)
		
	except Exception as e:
		flash(f"Lỗi khi tải file: {str(e)}", "danger")
		return redirect(url_for("pages.closing_standard_inventory"))


@pages.route("/closing/standard/inventory/export")
@permission_required("closing")
def closing_standard_inventory_export():
	"""Export inventories to Excel"""
	try:
		excel_data = export_inventories_to_excel()
		
		from flask import Response
		response = Response(
			excel_data,
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			headers={'Content-Disposition': 'attachment; filename=standard_inventory.xlsx'}
		)
		return response
		
	except Exception as e:
		flash(f"Lỗi khi xuất dữ liệu: {str(e)}", "danger")
		return redirect(url_for("pages.closing_standard_inventory"))


# API endpoints for closing module
@pages.route("/api/customers", methods=["GET"])
@permission_required("closing")
def api_customers():
	"""Get all customers for dropdown"""
	customers = list_customers()
	return jsonify(customers)


@pages.route("/api/samples-by-customer/<int:customer_id>", methods=["GET"])
@permission_required("closing")
def api_samples_by_customer(customer_id: int):
	"""Get samples by customer ID"""
	all_samples = list_samples()
	customer_samples = [s for s in all_samples if s.get("customer_id") == customer_id]
	return jsonify(customer_samples)