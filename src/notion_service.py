import requests
from config import NOTION_API_KEY, DATABASE_ID

url = "https://api.notion.com/v1/pages"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def create_task(task_name, due_date=None):
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": task_name
                    }
                }
            ]
        },
        "Done": {
            "checkbox": False
        }
    }

    # Si hay fecha, agregarla
    if due_date:
        properties["Due"] = {
            "date": {
                "start": str(due_date)
            }
        }

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }

    response = requests.post(url, json=data, headers=headers)
    
    return response.status_code, response.text

def get_tasks():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    payload = {
        "filter": {
            "property": "Done",
            "checkbox": {
                "equals": False
            }
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "ascending"
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return None, response.text

    data = response.json()

    tasks = []

    for item in data["results"]:
        try:
            title = item["properties"]["Name"]["title"]

            if title:
                task_name = title[0]["text"]["content"]
                task_id = item["id"]
                due = item["properties"].get("Due", {}).get("date")

                due_date = due["start"] if due else None

                task_done = item["properties"]["Done"]["checkbox"]

                tasks.append({
                    "id": task_id,
                    "name": task_name,
                    "done": task_done,
                    "due": due_date
                })
        except:
            continue

    return tasks, None

def mark_task_done(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    data = {
        "properties": {
            "Done": {
                "checkbox": True
            }
        }
    }

    response = requests.patch(url, json=data, headers=headers)

    return response.status_code, response.text

def delete_task(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"

    data = {
        "archived": True
    }

    response = requests.patch(url, json=data, headers=headers)

    return response.status_code, response.text