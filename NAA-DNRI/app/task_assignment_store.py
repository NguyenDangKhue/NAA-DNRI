import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TASK_ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "task_assignments.json")


def _ensure_store() -> None:
    """Đảm bảo thư mục data và file tồn tại"""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TASK_ASSIGNMENTS_FILE):
        with open(TASK_ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"task_assignments": []}, f, ensure_ascii=False, indent=2)


def load_task_assignments() -> List[Dict[str, Any]]:
    """Tải danh sách tất cả công việc được giao"""
    _ensure_store()
    with open(TASK_ASSIGNMENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("task_assignments", [])


def save_task_assignments(task_assignments: List[Dict[str, Any]]) -> None:
    """Lưu danh sách công việc được giao"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TASK_ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"task_assignments": task_assignments}, f, ensure_ascii=False, indent=2)


def get_next_task_id() -> int:
    """Lấy ID tiếp theo cho công việc mới"""
    tasks = load_task_assignments()
    if not tasks:
        return 1
    return max(task.get("id", 0) for task in tasks) + 1


def create_task_assignment(
    title: str,
    description: str,
    assigned_to: str,
    assigned_by: str,
    priority: str = "medium",
    due_date: str = None,
    category: str = None,
    note: str = None
) -> bool:
    """Tạo công việc mới được giao"""
    try:
        task_id = get_next_task_id()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        task_assignment = {
            "id": task_id,
            "title": title.strip(),
            "description": description.strip(),
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
            "priority": priority,
            "status": "pending",  # pending, in_progress, completed, cancelled
            "created_at": current_time,
            "updated_at": current_time,
            "due_date": due_date,
            "category": category,
            "note": note,
            "handover_history": []  # Lịch sử bàn giao
        }
        
        tasks = load_task_assignments()
        tasks.append(task_assignment)
        save_task_assignments(tasks)
        return True
    except Exception as e:
        print(f"Error creating task assignment: {e}")
        return False


def get_task_assignment(task_id: int) -> Optional[Dict[str, Any]]:
    """Lấy thông tin một công việc theo ID"""
    tasks = load_task_assignments()
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None


def update_task_assignment(
    task_id: int,
    title: str = None,
    description: str = None,
    assigned_to: str = None,
    priority: str = None,
    status: str = None,
    due_date: str = None,
    category: str = None,
    note: str = None
) -> bool:
    """Cập nhật thông tin công việc"""
    try:
        tasks = load_task_assignments()
        for task in tasks:
            if task.get("id") == task_id:
                if title is not None:
                    task["title"] = title.strip()
                if description is not None:
                    task["description"] = description.strip()
                if assigned_to is not None:
                    task["assigned_to"] = assigned_to
                if priority is not None:
                    task["priority"] = priority
                if status is not None:
                    task["status"] = status
                if due_date is not None:
                    task["due_date"] = due_date
                if category is not None:
                    task["category"] = category
                if note is not None:
                    task["note"] = note
                
                task["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_task_assignments(tasks)
                return True
        return False
    except Exception as e:
        print(f"Error updating task assignment: {e}")
        return False


def delete_task_assignment(task_id: int) -> bool:
    """Xóa công việc"""
    try:
        tasks = load_task_assignments()
        new_tasks = [task for task in tasks if task.get("id") != task_id]
        if len(new_tasks) == len(tasks):
            return False
        save_task_assignments(new_tasks)
        return True
    except Exception as e:
        print(f"Error deleting task assignment: {e}")
        return False


def get_tasks_by_user(username: str) -> List[Dict[str, Any]]:
    """Lấy danh sách công việc của một người dùng"""
    tasks = load_task_assignments()
    return [task for task in tasks if task.get("assigned_to") == username]


def get_tasks_assigned_by_user(username: str) -> List[Dict[str, Any]]:
    """Lấy danh sách công việc được giao bởi một người dùng"""
    tasks = load_task_assignments()
    return [task for task in tasks if task.get("assigned_by") == username]


def handover_task(task_id: int, from_user: str, to_user: str, handover_note: str = None) -> bool:
    """Bàn giao công việc từ người này sang người khác"""
    try:
        tasks = load_task_assignments()
        for task in tasks:
            if task.get("id") == task_id:
                # Kiểm tra quyền bàn giao
                if task.get("assigned_to") != from_user:
                    return False
                
                # Thêm vào lịch sử bàn giao
                handover_record = {
                    "from_user": from_user,
                    "to_user": to_user,
                    "handover_note": handover_note,
                    "handover_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if "handover_history" not in task:
                    task["handover_history"] = []
                task["handover_history"].append(handover_record)
                
                # Cập nhật người được giao
                task["assigned_to"] = to_user
                task["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Cập nhật tiêu đề công việc theo công đoạn
                original_title = task.get("original_title", task.get("title", ""))
                if not task.get("original_title"):
                    task["original_title"] = original_title
                
                # Đếm số lần bàn giao để xác định công đoạn
                handover_count = len(task.get("handover_history", []))
                stage_names = ["Nhận mẫu", "Đóng mẫu", "Chiếu mẫu", "Kiểm tra", "Hoàn thiện"]
                
                if handover_count < len(stage_names):
                    stage = stage_names[handover_count]
                    task["title"] = f"{original_title} - Công đoạn {handover_count + 1}: {stage}"
                else:
                    task["title"] = f"{original_title} - Công đoạn {handover_count + 1}: Xử lý tiếp"
                
                # Nếu công việc đã hoàn thành, reset về trạng thái pending để người nhận có thể tiếp tục
                if task.get("status") == "completed":
                    task["status"] = "pending"
                    task["completion_note"] = handover_note or "Đã bàn giao từ người hoàn thành"
                
                save_task_assignments(tasks)
                return True
        return False
    except Exception as e:
        print(f"Error handing over task: {e}")
        return False


def get_task_statistics(username: str = None) -> Dict[str, Any]:
    """Lấy thống kê công việc"""
    tasks = load_task_assignments()
    
    if username:
        tasks = [task for task in tasks if task.get("assigned_to") == username]
    
    stats = {
        "total": len(tasks),
        "pending": len([t for t in tasks if t.get("status") == "pending"]),
        "in_progress": len([t for t in tasks if t.get("status") == "in_progress"]),
        "completed": len([t for t in tasks if t.get("status") == "completed"]),
        "cancelled": len([t for t in tasks if t.get("status") == "cancelled"]),
        "high_priority": len([t for t in tasks if t.get("priority") == "high"]),
        "overdue": 0  # Có thể tính toán dựa trên due_date
    }
    
    # Tính số công việc quá hạn
    current_date = datetime.now().date()
    for task in tasks:
        if task.get("due_date") and task.get("status") not in ["completed", "cancelled"]:
            try:
                due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                if due_date < current_date:
                    stats["overdue"] += 1
            except:
                pass
    
    return stats


def get_tasks_paginated(page: int = 1, per_page: int = 20, status: str = None, priority: str = None, assigned_to: str = None) -> tuple:
    """Lấy danh sách công việc có phân trang và lọc"""
    tasks = load_task_assignments()
    
    # Lọc theo điều kiện
    if status:
        tasks = [task for task in tasks if task.get("status") == status]
    if priority:
        tasks = [task for task in tasks if task.get("priority") == priority]
    if assigned_to:
        tasks = [task for task in tasks if task.get("assigned_to") == assigned_to]
    
    # Sắp xếp theo ngày tạo mới nhất
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Phân trang
    total_count = len(tasks)
    total_pages = (total_count + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    paginated_tasks = tasks[start_index:end_index]
    
    return paginated_tasks, total_pages, total_count


def search_tasks(query: str, username: str = None) -> List[Dict[str, Any]]:
    """Tìm kiếm công việc theo từ khóa"""
    tasks = load_task_assignments()
    
    if username:
        tasks = [task for task in tasks if task.get("assigned_to") == username]
    
    query = query.lower().strip()
    if not query:
        return tasks
    
    results = []
    for task in tasks:
        if (query in task.get("title", "").lower() or 
            query in task.get("description", "").lower() or
            query in task.get("category", "").lower() or
            query in task.get("note", "").lower()):
            results.append(task)
    
    return results


def export_task_assignments_to_excel(username: str = None) -> str:
    """Xuất danh sách công việc ra CSV"""
    import io
    import csv
    
    tasks = load_task_assignments()
    if username:
        tasks = [task for task in tasks if task.get("assigned_to") == username]
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Tiêu đề', 'Mô tả', 'Người được giao', 'Người giao', 
        'Độ ưu tiên', 'Trạng thái', 'Ngày tạo', 'Hạn hoàn thành', 
        'Danh mục', 'Ghi chú'
    ])
    
    # Data
    for task in tasks:
        writer.writerow([
            task.get('id', ''),
            task.get('title', ''),
            task.get('description', ''),
            task.get('assigned_to', ''),
            task.get('assigned_by', ''),
            task.get('priority', ''),
            task.get('status', ''),
            task.get('created_at', ''),
            task.get('due_date', ''),
            task.get('category', ''),
            task.get('note', '')
        ])
    
    return output.getvalue()
