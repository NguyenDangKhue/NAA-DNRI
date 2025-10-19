import json
import os
from typing import Dict, Any, List, Optional
from werkzeug.security import generate_password_hash, check_password_hash


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


DEFAULT_SECTIONS = [
	"users",
	"customers",
	"receiving",
	"closing",
	"irradiation",
	"task_assignment",
]

# Định nghĩa các vai trò trong quy trình
WORKFLOW_ROLES = [
	("customer_info", "Nhận thông tin từ khách hàng"),
	("receiving", "Nhận mẫu"),
	("closing", "Đóng mẫu"),
	("irradiation", "Chiếu mẫu"),
	("task_assignment", "Giao việc")
]


def _ensure_store() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(USERS_FILE):
		seed_admin()


def seed_admin() -> None:
	"""Create the initial Admin user if file does not exist."""
	os.makedirs(DATA_DIR, exist_ok=True)
	admin_record = {
		"username": "Admin",
		"password_hash": generate_password_hash("admin"),
		"role": "admin",
		"permissions": DEFAULT_SECTIONS,
		"workflow_roles": [role[0] for role in WORKFLOW_ROLES],  # Admin có tất cả vai trò
		"active": True,
	}
	with open(USERS_FILE, "w", encoding="utf-8") as f:
		json.dump({"users": [admin_record]}, f, ensure_ascii=False, indent=2)


def load_users() -> List[Dict[str, Any]]:
	_ensure_store()
	with open(USERS_FILE, "r", encoding="utf-8") as f:
		data = json.load(f)
	return data.get("users", [])


def save_users(users: List[Dict[str, Any]]) -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	with open(USERS_FILE, "w", encoding="utf-8") as f:
		json.dump({"users": users}, f, ensure_ascii=False, indent=2)


def get_user(username: str) -> Optional[Dict[str, Any]]:
	for user in load_users():
		if user.get("username") == username:
			return user
	return None


def create_user(username: str, password: str, role: str, permissions: List[str], workflow_roles: List[str] = None, detailed_permissions: dict = None) -> bool:
	username = username.strip()
	if not username or get_user(username):
		return False
	
	# Xử lý permissions - nếu là admin thì có tất cả quyền
	if role == "admin":
		detailed_permissions = {section: "edit" for section in DEFAULT_SECTIONS}
		permissions = DEFAULT_SECTIONS
	else:
		# Chuyển đổi permissions cũ thành detailed_permissions nếu chưa có
		if detailed_permissions is None:
			detailed_permissions = {section: "view" if section in permissions else "none" for section in DEFAULT_SECTIONS}
	
	user = {
		"username": username,
		"password_hash": generate_password_hash(password),
		"role": role,
		"permissions": permissions,
		"detailed_permissions": detailed_permissions,
		"workflow_roles": workflow_roles or [],
		"active": True,
	}
	users = load_users()
	users.append(user)
	save_users(users)
	return True


def delete_user(username: str) -> bool:
	if username == "Admin":
		return False
	users = load_users()
	new_users = [u for u in users if u.get("username") != username]
	if len(new_users) == len(users):
		return False
	save_users(new_users)
	return True


def verify_user_credentials(username: str, password: str) -> bool:
	user = get_user(username)
	if not user or not user.get("active"):
		return False
	return check_password_hash(user.get("password_hash", ""), password)


def is_admin(username: str) -> bool:
	if username == "Admin":
		return True
	user = get_user(username)
	return bool(user and user.get("role") == "admin")


def has_permission(username: str, section: str) -> bool:
	if is_admin(username):
		return True
	user = get_user(username)
	if not user or not user.get("active"):
		return False
	return section in (user.get("permissions") or [])


def has_detailed_permission(username: str, section: str, permission_type: str = "view") -> bool:
	"""Kiểm tra quyền chi tiết của người dùng (view/edit/none)"""
	if is_admin(username):
		return True
	user = get_user(username)
	if not user or not user.get("active"):
		return False
	
	detailed_permissions = user.get("detailed_permissions", {})
	user_permission = detailed_permissions.get(section, "none")
	
	# Logic quyền: edit > view > none
	if permission_type == "edit":
		return user_permission == "edit"
	elif permission_type == "view":
		return user_permission in ["view", "edit"]
	else:
		return user_permission == permission_type


def get_user_permissions(username: str) -> dict:
	"""Lấy tất cả quyền chi tiết của người dùng"""
	if is_admin(username):
		return {section: "edit" for section in DEFAULT_SECTIONS}
	
	user = get_user(username)
	if not user or not user.get("active"):
		return {section: "none" for section in DEFAULT_SECTIONS}
	
	detailed_permissions = user.get("detailed_permissions", {})
	# Đảm bảo tất cả sections đều có quyền
	result = {}
	for section in DEFAULT_SECTIONS:
		result[section] = detailed_permissions.get(section, "none")
	return result


def has_workflow_role(username: str, workflow_role: str) -> bool:
	"""Kiểm tra xem người dùng có vai trò trong quy trình không"""
	if is_admin(username):
		return True
	user = get_user(username)
	if not user or not user.get("active"):
		return False
	return workflow_role in (user.get("workflow_roles") or [])


def update_user_workflow_roles(username: str, workflow_roles: List[str]) -> bool:
	"""Cập nhật vai trò quy trình cho người dùng"""
	users = load_users()
	for user in users:
		if user.get("username") == username:
			user["workflow_roles"] = workflow_roles
			save_users(users)
			return True
	return False


def get_workflow_roles() -> List[tuple]:
	"""Lấy danh sách các vai trò quy trình"""
	return WORKFLOW_ROLES


def update_user(username: str, password: str = None, role: str = None, permissions: List[str] = None, workflow_roles: List[str] = None, detailed_permissions: dict = None) -> bool:
	"""Cập nhật thông tin người dùng"""
	users = load_users()
	for user in users:
		if user.get("username") == username:
			if password:
				user["password_hash"] = generate_password_hash(password)
			if role:
				user["role"] = role
			if permissions is not None:
				user["permissions"] = permissions
			if workflow_roles is not None:
				user["workflow_roles"] = workflow_roles
			if detailed_permissions is not None:
				user["detailed_permissions"] = detailed_permissions
			save_users(users)
			return True
	return False


def update_user_password(username: str, new_password: str) -> bool:
	"""Cập nhật mật khẩu người dùng"""
	users = load_users()
	for user in users:
		if user.get("username") == username:
			user["password_hash"] = generate_password_hash(new_password)
			save_users(users)
			return True
	return False
