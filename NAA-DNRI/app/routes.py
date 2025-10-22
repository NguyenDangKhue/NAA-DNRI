from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import os

from .auth import login_required, verify_credentials, admin_required, permission_required
from .users_store import load_users, create_user, delete_user, DEFAULT_SECTIONS, get_workflow_roles, has_workflow_role, get_user, update_user, has_detailed_permission
from .task_assignment_store import (
    create_task_assignment, get_task_assignment, update_task_assignment, delete_task_assignment,
    get_tasks_by_user as get_assigned_tasks, get_tasks_assigned_by_user, handover_task,
    get_task_statistics, get_tasks_paginated, search_tasks, export_task_assignments_to_excel,
    get_task_stage_info, load_task_assignments, can_handover_task, is_workflow_completed,
    upload_task_file, get_task_files, delete_task_file
)
from .customers_store import list_customers, create_customer, delete_customer, get_customer, update_customer, export_customers_to_excel
from .samples_store import list_samples, list_samples_paginated, create_sample, delete_sample, get_sample, update_sample, import_samples_from_csv, export_samples_to_excel, save_filtered_samples_to_temp, load_filtered_samples_from_temp, cleanup_temp_file
from .closed_samples_store import list_closed_samples, list_closed_samples_paginated, create_closed_sample, delete_closed_sample, export_closed_samples_to_excel, import_closed_samples_from_csv
from .foil_store import list_foils, list_foils_paginated, create_foil, delete_foil, get_foil, update_foil, export_foils_to_excel, import_foils_from_csv
from .standard_store import list_standards, list_standards_paginated, create_standard, delete_standard, get_standard, update_standard, export_standards_to_excel, import_standards_from_csv
from .standard_inventory_store import list_inventories, list_inventories_paginated, create_inventory, delete_inventory, get_inventory, update_inventory, upload_certificate, get_certificate_path, export_inventories_to_excel
from .rotating_disk_store import list_rotating_disk_irradiations_paginated, create_rotating_disk_batch, delete_rotating_disk_batch, get_rotating_disk_batch, update_rotating_disk_batch, export_rotating_disk_irradiations_to_excel, create_rotating_disk_irradiation, get_rotating_disk_irradiation
from .channel_7_1_store import list_channel_7_1_irradiations, list_channel_7_1_irradiations_paginated, create_channel_7_1_irradiation, delete_channel_7_1_irradiation, get_channel_7_1_irradiation, update_channel_7_1_irradiation, export_channel_7_1_irradiations_to_excel
from .thermal_column_store import list_thermal_column_irradiations, list_thermal_column_irradiations_paginated, create_thermal_column_irradiation, delete_thermal_column_irradiation, get_thermal_column_irradiation, update_thermal_column_irradiation, export_thermal_column_irradiations_to_excel


pages = Blueprint("pages", __name__)


@pages.app_context_processor
def inject_permissions():
	"""Inject permission checking functions into template context"""
	def check_permission(section: str, permission_type: str = "view") -> bool:
		username = session.get("username")
		if not username:
			return False
		return has_detailed_permission(username, section, permission_type)
	
	return dict(has_permission=check_permission)


@pages.route("/", methods=["GET"])
@login_required
def index():
	username = session.get("username")
	
	# Lấy công việc từ module Giao việc
	my_assigned_tasks = get_assigned_tasks(username)
	task_stats = get_task_statistics(username)
	
	# Thêm thông tin giai đoạn cho mỗi công việc
	tasks_with_stages = []
	for task in my_assigned_tasks:
		stage_info = get_task_stage_info(task)
		task_with_stage = dict(task)
		task_with_stage['stage_info'] = stage_info
		task_with_stage['can_handover'] = can_handover_task(task)
		task_with_stage['is_workflow_completed'] = is_workflow_completed(task)
		tasks_with_stages.append(task_with_stage)
	
	return render_template("home.html", 
		username=username,
		my_assigned_tasks=tasks_with_stages,
		task_stats=task_stats
	)


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


# Users management (permission: users)
@pages.route("/users", methods=["GET"]) 
@permission_required("users")
def users_list():
	username = session.get("username")
	users = load_users()
	workflow_roles = get_workflow_roles()
	
	# Kiểm tra quyền chi tiết của người dùng hiện tại
	from .users_store import has_detailed_permission
	can_edit_users = has_detailed_permission(username, "users", "edit")
	
	return render_template("users/list.html", 
		users=users, 
		default_sections=DEFAULT_SECTIONS, 
		workflow_roles=workflow_roles, 
		workflow_roles_list=workflow_roles,
		can_edit_users=can_edit_users
	)


@pages.route("/users/create", methods=["POST"]) 
@permission_required("users")
def users_create():
	current_user = session.get("username")
	
	# Kiểm tra quyền chi tiết
	from .users_store import has_detailed_permission
	if not has_detailed_permission(current_user, "users", "edit"):
		flash("Bạn không có quyền tạo người dùng", "danger")
		return redirect(url_for("pages.users_list"))
	
	username = request.form.get("username", "").strip()
	password = request.form.get("password", "").strip()
	role = request.form.get("role", "user")
	workflow_roles = request.form.getlist("workflow_roles") or []
	
	# Xử lý detailed_permissions
	detailed_permissions = {}
	permissions = []
	
	if role == "admin":
		# Admin có tất cả quyền
		detailed_permissions = {section: "edit" for section in DEFAULT_SECTIONS}
		permissions = DEFAULT_SECTIONS
		workflow_roles = [role[0] for role in get_workflow_roles()]
	else:
		# Xử lý quyền chi tiết cho user thường
		for section in DEFAULT_SECTIONS:
			permission_value = request.form.get(f"detailed_permissions_{section}", "none")
			detailed_permissions[section] = permission_value
			if permission_value in ["view", "edit"]:
				permissions.append(section)
	
	if not username or not password:
		flash("Vui lòng nhập tên đăng nhập và mật khẩu", "warning")
		return redirect(url_for("pages.users_list"))
	
	if create_user(username, password, role, permissions, workflow_roles, detailed_permissions):
		flash("Tạo người dùng thành công", "success")
	else:
		flash("Tên đăng nhập đã tồn tại hoặc không hợp lệ", "danger")
	return redirect(url_for("pages.users_list"))


@pages.route("/users/delete/<username>", methods=["POST"]) 
@permission_required("users")
def users_delete(username: str):
	current_user = session.get("username")
	
	# Kiểm tra quyền chi tiết
	from .users_store import has_detailed_permission
	if not has_detailed_permission(current_user, "users", "edit"):
		flash("Bạn không có quyền xóa người dùng", "danger")
		return redirect(url_for("pages.users_list"))
	if delete_user(username):
		flash("Đã xoá người dùng", "success")
	else:
		flash("Không thể xoá người dùng này", "danger")
	return redirect(url_for("pages.users_list"))


@pages.route("/users/edit/<username>", methods=["GET"]) 
@permission_required("users")
def users_edit(username: str):
	current_user = session.get("username")
	
	# Kiểm tra quyền chi tiết
	from .users_store import has_detailed_permission
	if not has_detailed_permission(current_user, "users", "edit"):
		flash("Bạn không có quyền chỉnh sửa người dùng", "danger")
		return redirect(url_for("pages.users_list"))
	user = get_user(username)
	if not user:
		flash("Không tìm thấy người dùng", "danger")
		return redirect(url_for("pages.users_list"))
	
	workflow_roles = get_workflow_roles()
	can_edit_users = has_detailed_permission(current_user, "users", "edit")
	return render_template("users/edit.html", 
		user=user, 
		default_sections=DEFAULT_SECTIONS, 
		workflow_roles=workflow_roles,
		can_edit_users=can_edit_users
	)


@pages.route("/users/edit/<username>", methods=["POST"]) 
@permission_required("users")
def users_update(username: str):
	current_user = session.get("username")
	
	# Kiểm tra quyền chi tiết
	from .users_store import has_detailed_permission
	if not has_detailed_permission(current_user, "users", "edit"):
		flash("Bạn không có quyền chỉnh sửa người dùng", "danger")
		return redirect(url_for("pages.users_list"))
	user = get_user(username)
	if not user:
		flash("Không tìm thấy người dùng", "danger")
		return redirect(url_for("pages.users_list"))
	
	# Lấy dữ liệu từ form
	password = request.form.get("password", "").strip()
	role = request.form.get("role", "user")
	workflow_roles = request.form.getlist("workflow_roles") or []
	
	# Xử lý detailed_permissions
	detailed_permissions = {}
	permissions = []
	
	if role == "admin":
		# Admin có tất cả quyền
		detailed_permissions = {section: "edit" for section in DEFAULT_SECTIONS}
		permissions = DEFAULT_SECTIONS
		workflow_roles = [role[0] for role in get_workflow_roles()]
	else:
		# Xử lý quyền chi tiết cho user thường
		for section in DEFAULT_SECTIONS:
			permission_value = request.form.get(f"detailed_permissions_{section}", "none")
			detailed_permissions[section] = permission_value
			if permission_value in ["view", "edit"]:
				permissions.append(section)
	
	# Cập nhật thông tin
	update_data = {
		"role": role,
		"permissions": permissions,
		"workflow_roles": workflow_roles,
		"detailed_permissions": detailed_permissions
	}
	
	# Chỉ cập nhật mật khẩu nếu có nhập
	if password:
		update_data["password"] = password
	
	if update_user(username, **update_data):
		flash("Đã cập nhật người dùng thành công", "success")
	else:
		flash("Lỗi khi cập nhật người dùng", "danger")
	
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
		weight = float(request.form.get("weight", 0))
		moisture = float(request.form.get("moisture", 0))
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not standard_name or not box_name or weight <= 0:
			flash("Vui lòng nhập đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.closing_standard"))
		
		# Create standard
		create_standard(
			standard_name=standard_name,
			box_name=box_name,
			weight=weight,
			moisture=moisture,
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
		weight = float(request.form.get("weight", 0))
		moisture = float(request.form.get("moisture", 0))
		note = request.form.get("note", "").strip()
		
		# Validate required fields
		if not standard_name or not box_name or weight <= 0:
			flash("Vui lòng nhập đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.closing_standard_edit", standard_id=standard_id))
		
		# Update standard
		if update_standard(
			standard_id=standard_id,
			standard_name=standard_name,
			box_name=box_name,
			weight=weight,
			moisture=moisture,
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


@pages.route("/api/standard-inventory", methods=["GET"])
@permission_required("closing")
def api_standard_inventory():
	"""Get all standard inventories for dropdown"""
	inventories = list_inventories()
	return jsonify(inventories)


@pages.route("/api/samples-by-customer/<int:customer_id>", methods=["GET"])
@permission_required("closing")
def api_samples_by_customer(customer_id: int):
	"""Get samples by customer ID"""
	all_samples = list_samples()
	customer_samples = [s for s in all_samples if s.get("customer_id") == customer_id]
	return jsonify(customer_samples)


# Irradiation Module (permission: irradiation)
@pages.route("/irradiation", methods=["GET"]) 
@permission_required("irradiation")
def irradiation_index():
	"""Main irradiation module page with 3 sub-modules"""
	sub_modules = [
		("Chiếu mẫu mâm quay", "/irradiation/rotating-disk", "Quản lý chiếu mẫu trên mâm quay"),
		("Chiếu mẫu kênh 7-1", "/irradiation/channel-7-1", "Quản lý chiếu mẫu kênh 7-1"),
		("Chiếu mẫu cột nhiệt và 13-2", "/irradiation/thermal-column", "Quản lý chiếu mẫu cột nhiệt và 13-2")
	]
	return render_template("irradiation/index.html", sub_modules=sub_modules)


@pages.route("/irradiation/rotating-disk", methods=["GET"]) 
@permission_required("irradiation")
def irradiation_rotating_disk():
	"""Rotating disk irradiation management"""
	# Get pagination parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	
	# Get paginated rotating disk irradiation batches
	irradiation_batches, total_pages, total_count = list_rotating_disk_irradiations_paginated(page, per_page)
	
	return render_template("irradiation/rotating_disk.html", 
		irradiation_batches=irradiation_batches,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page
	)


@pages.route("/irradiation/channel-7-1", methods=["GET"]) 
@permission_required("irradiation")
def irradiation_channel_7_1():
	"""Channel 7-1 irradiation management"""
	# Get pagination parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	
	# Get paginated channel 7-1 irradiations
	irradiations, total_pages, total_count = list_channel_7_1_irradiations_paginated(page, per_page)
	
	return render_template("irradiation/channel_7_1.html", 
		irradiations=irradiations,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page
	)


@pages.route("/irradiation/thermal-column", methods=["GET"]) 
@permission_required("irradiation")
def irradiation_thermal_column():
	"""Thermal column irradiation management"""
	# Get pagination parameters
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	
	# Get paginated thermal column irradiations
	irradiations, total_pages, total_count = list_thermal_column_irradiations_paginated(page, per_page)
	
	return render_template("irradiation/thermal_column.html", 
		irradiations=irradiations,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page
	)


# Rotating Disk Irradiation Routes
@pages.route("/irradiation/rotating-disk/add", methods=["POST"])
@permission_required("irradiation")
def irradiation_rotating_disk_add():
	"""Add new rotating disk irradiation batch"""
	start_time = request.form.get("start_time", "").strip()
	irradiation_time = request.form.get("irradiation_time", "")
	power = request.form.get("power", "")
	batch_note = request.form.get("batch_note", "").strip()
	
	# Parse samples from form data
	samples = []
	sample_index = 0
	
	while True:
		sample_code = request.form.get(f"samples[{sample_index}][sample_code]", "").strip()
		sample_name = request.form.get(f"samples[{sample_index}][sample_name]", "").strip()
		disk_position = request.form.get(f"samples[{sample_index}][disk_position]", "")
		
		if not sample_code and not sample_name and not disk_position:
			break
			
		if not all([sample_code, sample_name, disk_position]):
			flash(f"Mẫu {sample_index + 1}: Vui lòng điền đầy đủ thông tin", "warning")
			return redirect(url_for("pages.irradiation_rotating_disk"))
		
		samples.append({
			'sample_code': sample_code,
			'sample_name': sample_name,
			'disk_position': int(disk_position)
		})
		sample_index += 1
	
	if not all([start_time, irradiation_time, power]):
		flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
		return redirect(url_for("pages.irradiation_rotating_disk"))
	
	if not samples:
		flash("Vui lòng thêm ít nhất một mẫu", "warning")
		return redirect(url_for("pages.irradiation_rotating_disk"))
	
	try:
		create_rotating_disk_batch(
			start_time=start_time,
			irradiation_time=float(irradiation_time),
			power=float(power),
			samples=samples,
			batch_note=batch_note
		)
		flash(f"Đã thêm lần chiếu mẫu với {len(samples)} mẫu", "success")
	except Exception as e:
		flash(f"Lỗi khi thêm lần chiếu mẫu: {str(e)}", "danger")
	
	return redirect(url_for("pages.irradiation_rotating_disk"))


@pages.route("/irradiation/rotating-disk/delete-batch/<int:batch_id>", methods=["POST"])
@permission_required("irradiation")
def irradiation_rotating_disk_delete_batch(batch_id: int):
	"""Delete rotating disk irradiation batch"""
	if delete_rotating_disk_batch(batch_id):
		flash("Đã xóa lần chiếu mẫu", "success")
	else:
		flash("Không tìm thấy lần chiếu để xóa", "danger")
	
	return redirect(url_for("pages.irradiation_rotating_disk"))


@pages.route("/irradiation/rotating-disk/delete/<int:irradiation_id>", methods=["POST"])
@permission_required("irradiation")
def irradiation_rotating_disk_delete(irradiation_id: int):
	"""Delete rotating disk irradiation batch"""
	if delete_rotating_disk_batch(irradiation_id):
		flash("Đã xóa lần chiếu mẫu", "success")
	else:
		flash("Không tìm thấy lần chiếu để xóa", "danger")
	
	return redirect(url_for("pages.irradiation_rotating_disk"))


# Channel 7-1 Irradiation Routes
@pages.route("/irradiation/channel-7-1/add", methods=["POST"])
@permission_required("irradiation")
def irradiation_channel_7_1_add():
	"""Add new channel 7-1 irradiation"""
	sample_code = request.form.get("sample_code", "").strip()
	sample_name = request.form.get("sample_name", "").strip()
	channel_position = request.form.get("channel_position", "").strip()
	irradiation_time = request.form.get("irradiation_time", "")
	power = request.form.get("power", "")
	temperature = request.form.get("temperature", "")
	note = request.form.get("note", "").strip()
	
	if not all([sample_code, sample_name, channel_position, irradiation_time, power]):
		flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
		return redirect(url_for("pages.irradiation_channel_7_1"))
	
	try:
		create_channel_7_1_irradiation(
			sample_code=sample_code,
			sample_name=sample_name,
			channel_position=channel_position,
			irradiation_time=float(irradiation_time),
			power=float(power),
			temperature=float(temperature) if temperature else None,
			note=note
		)
		flash("Đã thêm chiếu mẫu kênh 7-1", "success")
	except Exception as e:
		flash(f"Lỗi khi thêm chiếu mẫu: {str(e)}", "danger")
	
	return redirect(url_for("pages.irradiation_channel_7_1"))


@pages.route("/irradiation/channel-7-1/delete/<int:irradiation_id>", methods=["POST"])
@permission_required("irradiation")
def irradiation_channel_7_1_delete(irradiation_id: int):
	"""Delete channel 7-1 irradiation"""
	if delete_channel_7_1_irradiation(irradiation_id):
		flash("Đã xóa chiếu mẫu kênh 7-1", "success")
	else:
		flash("Không tìm thấy chiếu mẫu để xóa", "danger")
	
	return redirect(url_for("pages.irradiation_channel_7_1"))


# Thermal Column Irradiation Routes
@pages.route("/irradiation/thermal-column/add", methods=["POST"])
@permission_required("irradiation")
def irradiation_thermal_column_add():
	"""Add new thermal column irradiation"""
	sample_code = request.form.get("sample_code", "").strip()
	sample_name = request.form.get("sample_name", "").strip()
	irradiation_type = request.form.get("irradiation_type", "").strip()
	position = request.form.get("position", "").strip()
	irradiation_time = request.form.get("irradiation_time", "")
	power = request.form.get("power", "")
	temperature = request.form.get("temperature", "")
	pressure = request.form.get("pressure", "")
	note = request.form.get("note", "").strip()
	
	if not all([sample_code, sample_name, irradiation_type, irradiation_time, power]):
		flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
		return redirect(url_for("pages.irradiation_thermal_column"))
	
	try:
		create_thermal_column_irradiation(
			sample_code=sample_code,
			sample_name=sample_name,
			irradiation_type=irradiation_type,
			position=position,
			irradiation_time=float(irradiation_time),
			power=float(power),
			temperature=float(temperature) if temperature else None,
			pressure=float(pressure) if pressure else None,
			note=note
		)
		flash("Đã thêm chiếu mẫu cột nhiệt và 13-2", "success")
	except Exception as e:
		flash(f"Lỗi khi thêm chiếu mẫu: {str(e)}", "danger")
	
	return redirect(url_for("pages.irradiation_thermal_column"))


# Task Assignment Module (permission: task_assignment)
@pages.route("/task-assignment", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_index():
	"""Trang chính module Giao việc"""
	username = session.get("username")
	
	# Lấy thống kê
	stats = get_task_statistics(username)
	
	# Lấy danh sách công việc gần đây
	recent_tasks, _, _ = get_tasks_paginated(page=1, per_page=5, assigned_to=username)
	
	return render_template("task_assignment/index.html", 
		username=username,
		stats=stats,
		recent_tasks=recent_tasks
	)


@pages.route("/task-assignment/list", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_list():
	"""Danh sách tất cả công việc"""
	# Lấy tham số phân trang và lọc
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	status = request.args.get('status', '')
	priority = request.args.get('priority', '')
	assigned_to = request.args.get('assigned_to', '')
	search_query = request.args.get('search', '')
	
	# Lấy danh sách người dùng để hiển thị trong dropdown
	all_users = load_users()
	
	# Lấy danh sách công việc
	if search_query:
		tasks = search_tasks(search_query)
		total_pages = 1
		total_count = len(tasks)
	else:
		tasks, total_pages, total_count = get_tasks_paginated(page, per_page, status, priority, assigned_to)
	
	# Thêm thông tin giai đoạn cho mỗi công việc
	tasks_with_stages = []
	for task in tasks:
		stage_info = get_task_stage_info(task)
		task_with_stage = dict(task)
		task_with_stage['stage_info'] = stage_info
		task_with_stage['can_handover'] = can_handover_task(task)
		task_with_stage['is_workflow_completed'] = is_workflow_completed(task)
		tasks_with_stages.append(task_with_stage)
	
	return render_template("task_assignment/list.html", 
		tasks=tasks_with_stages,
		all_users=all_users,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_status=status,
		selected_priority=priority,
		selected_assigned_to=assigned_to,
		search_query=search_query
	)


@pages.route("/task-assignment/my-tasks", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_my_tasks():
	"""Công việc của tôi"""
	username = session.get("username")
	
	# Lấy tham số phân trang và lọc
	page = int(request.args.get('page', 1))
	per_page = int(request.args.get('per_page', 20))
	status = request.args.get('status', '')
	priority = request.args.get('priority', '')
	search_query = request.args.get('search', '')
	
	# Lấy danh sách công việc của người dùng
	if search_query:
		tasks = search_tasks(search_query, username)
		total_pages = 1
		total_count = len(tasks)
	else:
		tasks, total_pages, total_count = get_tasks_paginated(page, per_page, status, priority, username)
	
	# Lấy thống kê cá nhân
	stats = get_task_statistics(username)
	
	# Thêm thông tin giai đoạn và can_handover cho mỗi công việc
	tasks_with_stages = []
	for task in tasks:
		stage_info = get_task_stage_info(task)
		task_with_stage = dict(task)
		task_with_stage['stage_info'] = stage_info
		task_with_stage['can_handover'] = can_handover_task(task)
		task_with_stage['is_workflow_completed'] = is_workflow_completed(task)
		tasks_with_stages.append(task_with_stage)
	
	return render_template("task_assignment/my_tasks.html", 
		tasks=tasks_with_stages,
		username=username,
		stats=stats,
		current_page=page,
		total_pages=total_pages,
		total_count=total_count,
		per_page=per_page,
		selected_status=status,
		selected_priority=priority,
		search_query=search_query
	)


@pages.route("/task-assignment/create", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_create_form():
	"""Form tạo công việc mới hoặc lặp lại công đoạn"""
	all_users = load_users()
	
	# Lấy danh sách công việc hiện có để có thể lặp lại công đoạn
	existing_tasks = load_task_assignments()
	
	return render_template("task_assignment/create.html", 
		all_users=all_users,
		existing_tasks=existing_tasks
	)


@pages.route("/task-assignment/create", methods=["POST"]) 
@permission_required("task_assignment")
def task_assignment_create():
	"""Tạo công việc mới hoặc lặp lại công đoạn"""
	username = session.get("username")
	task_type = request.form.get("task_type", "new")
	
	if task_type == "new":
		# Tạo công việc mới
		title = request.form.get("title", "").strip()
		description = request.form.get("description", "").strip()
		assigned_to = request.form.get("assigned_to", "").strip()
		priority = request.form.get("priority", "medium")
		due_date = request.form.get("due_date", "")
		category = request.form.get("category", "").strip()
		note = request.form.get("note", "").strip()
		
		if not all([title, description, assigned_to]):
			flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.task_assignment_create_form"))
		
		if create_task_assignment(
			title=title,
			description=description,
			assigned_to=assigned_to,
			assigned_by=username,
			priority=priority,
			due_date=due_date if due_date else None,
			category=category if category else None,
			note=note if note else None
		):
			flash("Đã tạo công việc thành công", "success")
			return redirect(url_for("pages.task_assignment_list"))
		else:
			flash("Lỗi khi tạo công việc", "danger")
			return redirect(url_for("pages.task_assignment_create_form"))
	
	elif task_type == "repeat":
		# Lặp lại công đoạn
		existing_task_id = request.form.get("existing_task_id", "").strip()
		stage_to_repeat = request.form.get("stage_to_repeat", "").strip()
		assigned_to = request.form.get("assigned_to", "").strip()
		priority = request.form.get("priority", "medium")
		due_date = request.form.get("due_date", "")
		category = request.form.get("category", "").strip()
		repeat_reason = request.form.get("repeat_reason", "").strip()
		
		if not all([existing_task_id, stage_to_repeat, assigned_to]):
			flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
			return redirect(url_for("pages.task_assignment_create_form"))
		
		# Lấy thông tin công việc gốc
		original_task = get_task_assignment(int(existing_task_id))
		if not original_task:
			flash("Không tìm thấy công việc gốc", "danger")
			return redirect(url_for("pages.task_assignment_create_form"))
		
		# Tạo tiêu đề cho công việc lặp lại
		stage_names = {
			'nhan_mau': 'Nhận mẫu',
			'dong_mau': 'Đóng mẫu', 
			'chieu_mau': 'Chiếu mẫu',
			'xu_ly_so_lieu': 'Xử lý số liệu',
			'kiem_tra_duyet': 'Kiểm tra và duyệt kết quả'
		}
		stage_name = stage_names.get(stage_to_repeat, stage_to_repeat)
		
		title = f"{original_task.get('title', '')} - Lặp lại: {stage_name}"
		description = f"Lặp lại công đoạn '{stage_name}' cho công việc #{existing_task_id}"
		if repeat_reason:
			description += f"\n\nLý do: {repeat_reason}"
		
		if create_task_assignment(
			title=title,
			description=description,
			assigned_to=assigned_to,
			assigned_by=username,
			priority=priority,
			due_date=due_date if due_date else None,
			category=category if category else None,
			note=f"Lặp lại công đoạn từ công việc #{existing_task_id}. {repeat_reason}" if repeat_reason else f"Lặp lại công đoạn từ công việc #{existing_task_id}"
		):
			flash(f"Đã tạo công việc lặp lại công đoạn '{stage_name}' thành công", "success")
			return redirect(url_for("pages.task_assignment_list"))
		else:
			flash("Lỗi khi tạo công việc lặp lại", "danger")
			return redirect(url_for("pages.task_assignment_create_form"))
	
	else:
		flash("Loại công việc không hợp lệ", "danger")
		return redirect(url_for("pages.task_assignment_create_form"))


@pages.route("/task-assignment/<int:task_id>/edit", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_edit_form(task_id):
	"""Form chỉnh sửa công việc"""
	task = get_task_assignment(task_id)
	if not task:
		flash("Không tìm thấy công việc", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	all_users = load_users()
	return render_template("task_assignment/edit.html", task=task, all_users=all_users)


@pages.route("/task-assignment/<int:task_id>/edit", methods=["POST"]) 
@permission_required("task_assignment")
def task_assignment_edit(task_id):
	"""Cập nhật công việc"""
	task = get_task_assignment(task_id)
	if not task:
		flash("Không tìm thấy công việc", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	title = request.form.get("title", "").strip()
	description = request.form.get("description", "").strip()
	assigned_to = request.form.get("assigned_to", "").strip()
	priority = request.form.get("priority", "medium")
	status = request.form.get("status", "pending")
	due_date = request.form.get("due_date", "")
	category = request.form.get("category", "").strip()
	note = request.form.get("note", "").strip()
	
	if not all([title, description, assigned_to]):
		flash("Vui lòng điền đầy đủ thông tin bắt buộc", "warning")
		return redirect(url_for("pages.task_assignment_edit_form", task_id=task_id))
	
	if update_task_assignment(
		task_id=task_id,
		title=title,
		description=description,
		assigned_to=assigned_to,
		priority=priority,
		status=status,
		due_date=due_date if due_date else None,
		category=category if category else None,
		note=note if note else None
	):
		flash("Đã cập nhật công việc thành công", "success")
	else:
		flash("Lỗi khi cập nhật công việc", "danger")
	
	return redirect(url_for("pages.task_assignment_list"))


@pages.route("/task-assignment/<int:task_id>/delete", methods=["POST"]) 
@permission_required("task_assignment")
def task_assignment_delete(task_id):
	"""Xóa công việc"""
	if delete_task_assignment(task_id):
		flash("Đã xóa công việc thành công", "success")
	else:
		flash("Không tìm thấy công việc để xóa", "danger")
	
	return redirect(url_for("pages.task_assignment_list"))


@pages.route("/task-assignment/<int:task_id>/handover", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_handover_form(task_id):
	"""Form bàn giao công việc"""
	task = get_task_assignment(task_id)
	if not task:
		flash("Không tìm thấy công việc", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	username = session.get("username")
	if task.get("assigned_to") != username:
		flash("Bạn không có quyền bàn giao công việc này", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	# Kiểm tra xem có thể bàn giao được không
	if not can_handover_task(task):
		flash("Công việc này đã hoàn thành toàn bộ quy trình và không thể bàn giao tiếp", "warning")
		return redirect(url_for("pages.task_assignment_detail", task_id=task_id))
	
	all_users = load_users()
	return render_template("task_assignment/handover.html", task=task, all_users=all_users)


@pages.route("/task-assignment/<int:task_id>/handover", methods=["POST"]) 
@permission_required("task_assignment")
def task_assignment_handover(task_id):
	"""Bàn giao công việc"""
	username = session.get("username")
	to_user = request.form.get("to_user", "").strip()
	handover_note = request.form.get("handover_note", "").strip()
	
	# Kiểm tra công việc có tồn tại không
	task = get_task_assignment(task_id)
	if not task:
		flash("Không tìm thấy công việc", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	# Kiểm tra quyền bàn giao
	if task.get("assigned_to") != username:
		flash("Bạn không có quyền bàn giao công việc này", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	# Kiểm tra xem có thể bàn giao được không
	if not can_handover_task(task):
		flash("Công việc này đã hoàn thành toàn bộ quy trình và không thể bàn giao tiếp", "warning")
		return redirect(url_for("pages.task_assignment_detail", task_id=task_id))
	
	if not to_user:
		flash("Vui lòng chọn người nhận bàn giao", "warning")
		return redirect(url_for("pages.task_assignment_handover_form", task_id=task_id))
	
	if handover_task(task_id, username, to_user, handover_note):
		flash("Đã bàn giao công việc thành công", "success")
		return redirect(url_for("pages.task_assignment_my_tasks"))
	else:
		flash("Lỗi khi bàn giao công việc", "danger")
		return redirect(url_for("pages.task_assignment_handover_form", task_id=task_id))


@pages.route("/task-assignment/<int:task_id>/detail", methods=["GET"]) 
@permission_required("task_assignment")
def task_assignment_detail(task_id):
	"""Chi tiết công việc với sơ đồ công việc"""
	task = get_task_assignment(task_id)
	if not task:
		flash("Không tìm thấy công việc", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	# Lấy danh sách người dùng để hiển thị tên
	all_users = load_users()
	user_names = {user["username"]: user["username"] for user in all_users}
	
	# Chuẩn bị dữ liệu cho sơ đồ công việc
	workflow_stages = ["Nhận mẫu", "Đóng mẫu", "Chiếu mẫu", "Xử lý số liệu", "Kiểm tra và duyệt kết quả"]
	handover_history = task.get("handover_history", [])
	
	# Tạo timeline cho sơ đồ
	timeline = []
	
	# Thêm bước đầu tiên (người giao ban đầu)
	timeline.append({
		"stage": "Khởi tạo",
		"user": task.get("assigned_by", "Unknown"),
		"date": task.get("created_at", ""),
		"status": "completed",
		"note": "Công việc được tạo"
	})
	
	# Thêm các bước bàn giao
	for i, handover in enumerate(handover_history):
		if i < len(workflow_stages):
			stage_name = workflow_stages[i]
		elif i == len(workflow_stages):
			stage_name = "Lưu kết quả"
		else:
			stage_name = f"Công đoạn {i+1}"
		
		timeline.append({
			"stage": stage_name,
			"user": handover.get("from_user", "Unknown"),
			"date": handover.get("handover_date", ""),
			"status": "completed",
			"note": handover.get("handover_note", ""),
			"handover_to": handover.get("to_user", "Unknown")
		})
	
	# Thêm bước hiện tại
	current_stage_index = len(handover_history)
	if current_stage_index < len(workflow_stages):
		current_stage = workflow_stages[current_stage_index]
	elif current_stage_index == len(workflow_stages):
		current_stage = "Lưu kết quả"
	else:
		current_stage = f"Công đoạn {current_stage_index + 1}"
	
	timeline.append({
		"stage": current_stage,
		"user": task.get("assigned_to", "Unknown"),
		"date": task.get("updated_at", ""),
		"status": task.get("status", "pending"),
		"note": "Đang xử lý",
		"is_current": True
	})
	
	return render_template("task_assignment/detail.html", 
		task=task,
		timeline=timeline,
		user_names=user_names,
		can_handover=can_handover_task(task),
		is_workflow_completed=is_workflow_completed(task)
	)


@pages.route("/task-assignment/<int:task_id>/status", methods=["POST"]) 
@permission_required("task_assignment")
def task_assignment_update_status(task_id):
	"""Cập nhật trạng thái công việc"""
	username = session.get("username")
	status = request.form.get("status", "").strip()
	
	if not status:
		flash("Trạng thái không hợp lệ", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	task = get_task_assignment(task_id)
	if not task:
		flash("Không tìm thấy công việc", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	# Kiểm tra quyền cập nhật (chỉ người được giao việc mới có thể cập nhật trạng thái)
	if task.get("assigned_to") != username:
		flash("Bạn không có quyền cập nhật công việc này", "danger")
		return redirect(url_for("pages.task_assignment_list"))
	
	if update_task_assignment(task_id, status=status):
		flash("Đã cập nhật trạng thái công việc", "success")
	else:
		flash("Lỗi khi cập nhật công việc", "danger")
	
	return redirect(url_for("pages.task_assignment_my_tasks"))


@pages.route("/task-assignment/export")
@permission_required("task_assignment")
def task_assignment_export():
	"""Xuất danh sách công việc ra Excel"""
	from flask import Response
	from urllib.parse import quote
	
	try:
		# Xuất công việc ra CSV format
		csv_content = export_task_assignments_to_excel()
		
		# Tạo filename với timestamp
		from datetime import datetime
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"danh_sach_giao_viec_{timestamp}.csv"
		
		# Return với proper headers cho Excel compatibility
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
		return redirect(url_for("pages.task_assignment_list"))


@pages.route("/task-assignment/my-tasks/export")
@permission_required("task_assignment")
def task_assignment_my_tasks_export():
	"""Xuất công việc của tôi ra Excel"""
	from flask import Response
	from urllib.parse import quote
	
	try:
		username = session.get("username")
		# Xuất công việc của người dùng hiện tại
		csv_content = export_task_assignments_to_excel(username)
		
		# Tạo filename với timestamp
		from datetime import datetime
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"cong_viec_cua_toi_{username}_{timestamp}.csv"
		
		# Return với proper headers cho Excel compatibility
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
		return redirect(url_for("pages.task_assignment_my_tasks"))


# File Upload Routes
@pages.route("/task-assignment/<int:task_id>/upload", methods=["POST"])
@permission_required("task_assignment")
def task_assignment_upload_file(task_id):
    """Upload file cho công việc"""
    username = session.get("username")
    task = get_task_assignment(task_id)
    
    if not task:
        flash("Không tìm thấy công việc", "danger")
        return redirect(url_for("pages.task_assignment_list"))
    
    # Kiểm tra quyền upload (chỉ người được giao việc mới có thể upload)
    if task.get("assigned_to") != username:
        flash("Bạn không có quyền upload file cho công việc này", "danger")
        return redirect(url_for("pages.task_assignment_detail", task_id=task_id))
    
    # Lấy thông tin từ form
    file = request.files.get("file")
    stage_name = request.form.get("stage_name", "").strip()
    description = request.form.get("description", "").strip()
    
    if not file or not file.filename:
        flash("Vui lòng chọn file để upload", "warning")
        return redirect(url_for("pages.task_assignment_detail", task_id=task_id))
    
    if not stage_name:
        flash("Vui lòng chọn công đoạn", "warning")
        return redirect(url_for("pages.task_assignment_detail", task_id=task_id))
    
    # Upload file
    result = upload_task_file(task_id, file, stage_name, username, description)
    
    if result["success"]:
        flash(f"Đã upload file '{result['file_info']['original_filename']}' thành công", "success")
    else:
        flash(f"Lỗi upload file: {result['error']}", "danger")
    
    return redirect(url_for("pages.task_assignment_detail", task_id=task_id))


@pages.route("/task-assignment/<int:task_id>/files")
@permission_required("task_assignment")
def task_assignment_files(task_id):
    """Xem danh sách file của công việc"""
    task = get_task_assignment(task_id)
    if not task:
        flash("Không tìm thấy công việc", "danger")
        return redirect(url_for("pages.task_assignment_list"))
    
    files = get_task_files(task_id)
    stage_name = request.args.get("stage", "")
    
    if stage_name:
        files = [f for f in files if f.get("stage_name") == stage_name]
    
    return render_template("task_assignment/files.html", 
        task=task, 
        files=files, 
        selected_stage=stage_name
    )


@pages.route("/task-assignment/<int:task_id>/files/<file_id>/download")
@permission_required("task_assignment")
def task_assignment_download_file(task_id, file_id):
    """Download file của công việc"""
    from flask import send_file, abort
    
    task = get_task_assignment(task_id)
    if not task:
        abort(404)
    
    files = get_task_files(task_id)
    file_info = next((f for f in files if f.get("id") == file_id), None)
    
    if not file_info:
        abort(404)
    
    file_path = file_info.get("file_path")
    if not file_path or not os.path.exists(file_path):
        abort(404)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_info.get("original_filename", "file")
    )


@pages.route("/task-assignment/<int:task_id>/files/<file_id>/delete", methods=["POST"])
@permission_required("task_assignment")
def task_assignment_delete_file(task_id, file_id):
    """Xóa file của công việc"""
    username = session.get("username")
    task = get_task_assignment(task_id)
    
    if not task:
        flash("Không tìm thấy công việc", "danger")
        return redirect(url_for("pages.task_assignment_list"))
    
    # Kiểm tra quyền xóa (chỉ người được giao việc mới có thể xóa)
    if task.get("assigned_to") != username:
        flash("Bạn không có quyền xóa file của công việc này", "danger")
        return redirect(url_for("pages.task_assignment_detail", task_id=task_id))
    
    if delete_task_file(task_id, file_id):
        flash("Đã xóa file thành công", "success")
    else:
        flash("Lỗi khi xóa file", "danger")
    
    return redirect(url_for("pages.task_assignment_detail", task_id=task_id))