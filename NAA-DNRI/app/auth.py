from functools import wraps
from typing import Callable, Any, Optional

from flask import session, redirect, url_for, abort

from .users_store import verify_user_credentials, is_admin as _is_admin, has_permission as _has_permission


ADMIN_USERNAME = "Admin"


def verify_credentials(username: str, password: str) -> bool:
	return verify_user_credentials(username, password)


def login_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
	@wraps(view_func)
	def wrapped(*args: Any, **kwargs: Any):
		if not session.get("user_id"):
			return redirect(url_for("pages.login"))
		return view_func(*args, **kwargs)

	return wrapped


def admin_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
	@wraps(view_func)
	def wrapped(*args: Any, **kwargs: Any):
		username: Optional[str] = session.get("user_id")
		if not username:
			return redirect(url_for("pages.login"))
		if not _is_admin(username):
			return abort(403)
		return view_func(*args, **kwargs)

	return wrapped


def permission_required(section: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
		@wraps(view_func)
		def wrapped(*args: Any, **kwargs: Any):
			username: Optional[str] = session.get("user_id")
			if not username:
				return redirect(url_for("pages.login"))
			if not _has_permission(username, section):
				return abort(403)
			return view_func(*args, **kwargs)

		return wrapped

	return decorator
