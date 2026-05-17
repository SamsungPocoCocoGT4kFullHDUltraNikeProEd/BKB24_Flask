import sys
import io
import contextlib
from itertools import cycle
import datetime
from flask import Flask, jsonify, request

status_lst = ["cancelled", "completed", "in_progress", "pending"]
priority_lst = ["high", "low", "medium"]

def get_task_list():
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        import this
    text = f.getvalue()
    status_cycle = cycle(status_lst)
    priority_cycle = cycle(priority_lst)
    tasks_lst = []
    num = 0
    for line in text.splitlines():
        if not line:
            continue
        num += 1
        tasks_lst.append({
            "id": num,
            "title": "Zen of Python",
            "description": line,
            "status": next(status_cycle),
            "priority": next(priority_cycle),
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "deleted_at": None,
        })
    return tasks_lst

tasks_lst = get_task_list()

app = Flask(__name__)


def now_iso():
    return datetime.datetime.now().isoformat()


def find_task(task_id):
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        return None
    for task in tasks_lst:
        if task["id"] == task_id:
            return task
    return None


@app.route("/api/v1/tasks", methods=["GET"])
def get_tasks_lst():
    query = request.args.get("query")
    order = request.args.get("order", "id")
    offset = request.args.get("offset", 0)

    try:
        offset = int(offset)
    except (TypeError, ValueError):
        offset = 0

    reverse = False
    if order.startswith("-"):
        reverse = True
        order = order[1:]

    allowed_order_fields = {
        "id",
        "title",
        "description",
        "status",
        "priority",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    if order not in allowed_order_fields:
        order = "id"

    result = tasks_lst[:]

    if query:
        query_lower = query.lower()
        result = [
            task
            for task in result
            if query_lower in task["title"].lower()
            or query_lower in task["description"].lower()
        ]

    result = sorted(
        result,
        key=lambda x: (x.get(order) is None, x.get(order)),
        reverse=reverse,
    )

    result = result[offset:offset + 10]

    return jsonify({"tasks": result})


@app.route("/api/v1/tasks/<task_id>", methods=["GET"])
def get_tasks(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": "Задача не найдена"}), 404
    return jsonify(task)


@app.route("/api/v1/tasks", methods=["POST"])
def post_tasks():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Отсутствуют данные JSON"}), 400

    title = data.get("title")
    description = data.get("description")
    status = data.get("status", "pending")
    priority = data.get("priority", "medium")

    if title is None:
        return jsonify({"error": "Пропущен обязательный параметр `title`"}), 400

    if description is None:
        return jsonify({"error": "Пропущен обязательный параметр `description`"}), 400

    if status not in status_lst:
        return jsonify({"error": "Поле `status` невалидно"}), 400

    if priority not in priority_lst:
        return jsonify({"error": "Поле `priority` невалидно"}), 400

    current_time = now_iso()
    task = {
        "id": len(tasks_lst) + 1,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "created_at": current_time,
        "updated_at": current_time,
        "deleted_at": None,
    }

    tasks_lst.append(task)
    return jsonify(task)


@app.route("/api/v1/tasks/<task_id>", methods=["DELETE"])
def delete_tasks(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": "Задача не найдена"}), 404

    current_time = now_iso()
    task["status"] = "cancelled"
    task["updated_at"] = current_time
    task["deleted_at"] = current_time

    return jsonify(task)


@app.route("/api/v1/tasks/<task_id>", methods=["PATCH"])
def patch_tasks(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": "Задача не найдена"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Отсутствуют данные JSON"}), 400

    if "status" in data and data["status"] not in status_lst:
        return jsonify({"error": "Поле `status` невалидно"}), 400

    if "priority" in data and data["priority"] not in priority_lst:
        return jsonify({"error": "Поле `priority` невалидно"}), 400

    for field in ("title", "description", "status", "priority"):
        if field in data:
            task[field] = data[field]

    task["updated_at"] = now_iso()

    return jsonify(task)

if __name__ == "__main__":
    app.run(debug=True)