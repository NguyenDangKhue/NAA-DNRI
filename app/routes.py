from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from .auth import login_required, verify_credentials, admin_required, permission_required
from .users_store import load_users, create_user, delete_user, DEFAULT_SECTIONS
from .customers_store import list_customers, create_customer, delete_customer, get_customer, update_customer, export_customers_to_excel
from .samples_store import list_samples, list_samples_paginated, create_sample, delete_sample, get_sample, update_sample, import_samples_from_csv, export_samples_to_excel, save_filtered_samples_to_temp, load_filtered_samples_from_temp, cleanup_temp_file
from .closed_samples_store import list_closed_samples, create_closed_sample, delete_closed_sample, export_closed_samples_to_excel


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
	create_sample(int(customer_id), sample_name, sample_code, sample_type, analysis_target, note)
	flash("Đã thêm mẫu", "success")
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
	if update_sample(sample_id, int(customer_id), sample_name, sample_code, sample_type, analysis_target, note):
		flash("Đã cập nhật mẫu", "success")
	else:
		flash("Cập nhật thất bại", "danger")
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
	closed_samples = list_closed_samples()
	return render_template("closing/regular.html", closed_samples=closed_samples)


@pages.route("/closing/regular/add", methods=["POST"])
@permission_required("closing")
def closing_regular_add():
	"""Add a new closed sample with multiple boxes"""
	try:
		closing_date = request.form.get("closing_date")
		customer_name = request.form.get("customer_name")
		sample_name = request.form.get("sample_name")
		encoding = request.form.get("encoding")
		note = request.form.get("note", "")
		
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
		
		# Create closed samples with boxes
		from .closed_samples_store import create_closed_sample_with_boxes
		created_ids = create_closed_sample_with_boxes(
			closing_date=closing_date,
			customer_name=customer_name,
			sample_name=sample_name,
			encoding=encoding,
			boxes=boxes,
			note=note
		)
		
		flash(f"Đã thêm mẫu đóng thành công với {len(created_ids)} box!", "success")
		return redirect(url_for("pages.closing_regular"))
		
	except Exception as e:
		flash(f"Lỗi khi thêm mẫu đóng: {str(e)}", "danger")
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


@pages.route("/closing/foil", methods=["GET"]) 
@permission_required("closing")
def closing_foil():
	"""Foil sample closing management"""
	return render_template("closing/foil.html")


@pages.route("/closing/standard", methods=["GET"]) 
@permission_required("closing")
def closing_standard():
	"""Standard sample closing management"""
	return render_template("closing/standard.html")