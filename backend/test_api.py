"""Quick test script for Agent Rangers API."""

import asyncio
import json
from uuid import UUID

import httpx


BASE_URL = "http://localhost:8000"


async def test_api():
    """Test the Agent Rangers API endpoints."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("=" * 60)
        print("Testing Agent Rangers API")
        print("=" * 60)

        # Test health endpoint
        print("\n1. Testing health check...")
        response = await client.get("/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200

        # Create a board
        print("\n2. Creating a board...")
        board_data = {
            "name": "Test Board",
            "description": "A test Kanban board",
            "settings": {"theme": "dark"},
        }
        response = await client.post("/api/boards", json=board_data)
        print(f"Status: {response.status_code}")
        board = response.json()
        print(f"Created board: {board['id']}")
        assert response.status_code == 201
        board_id = board["id"]

        # Get all boards
        print("\n3. Getting all boards...")
        response = await client.get("/api/boards")
        print(f"Status: {response.status_code}")
        boards = response.json()
        print(f"Found {len(boards)} board(s)")
        assert response.status_code == 200
        assert len(boards) >= 1

        # Create columns
        print("\n4. Creating columns...")
        columns_data = [
            {"name": "Backlog", "color": "#6366f1"},
            {"name": "In Progress", "color": "#22c55e"},
            {"name": "Done", "color": "#84cc16"},
        ]
        column_ids = []
        for col_data in columns_data:
            response = await client.post(
                f"/api/boards/{board_id}/columns", json=col_data
            )
            print(f"Created column: {response.json()['name']}")
            assert response.status_code == 201
            column_ids.append(response.json()["id"])

        # Get board with columns
        print("\n5. Getting board with columns...")
        response = await client.get(f"/api/boards/{board_id}")
        print(f"Status: {response.status_code}")
        board_with_cols = response.json()
        print(f"Board has {len(board_with_cols['columns'])} column(s)")
        assert response.status_code == 200
        assert len(board_with_cols["columns"]) == 3

        # Create tasks
        print("\n6. Creating tasks...")
        tasks_data = [
            {
                "title": "Task 1",
                "description": "First test task",
                "column_id": column_ids[0],
                "priority": 2,
                "labels": ["backend", "api"],
            },
            {
                "title": "Task 2",
                "description": "Second test task",
                "column_id": column_ids[0],
                "priority": 3,
                "labels": ["frontend"],
            },
        ]
        task_ids = []
        for task_data in tasks_data:
            response = await client.post(
                f"/api/boards/{board_id}/tasks", json=task_data
            )
            print(f"Created task: {response.json()['title']}")
            assert response.status_code == 201
            task_ids.append(response.json()["id"])

        # Get all tasks
        print("\n7. Getting all tasks...")
        response = await client.get(f"/api/boards/{board_id}/tasks")
        print(f"Status: {response.status_code}")
        tasks = response.json()
        print(f"Found {len(tasks)} task(s)")
        assert response.status_code == 200
        assert len(tasks) == 2

        # Update a task
        print("\n8. Updating a task...")
        task_id = task_ids[0]
        response = await client.get(f"/api/tasks/{task_id}")
        task = response.json()
        update_data = {
            "title": "Updated Task 1",
            "priority": 4,
            "version": task["version"],
        }
        response = await client.put(f"/api/tasks/{task_id}", json=update_data)
        print(f"Status: {response.status_code}")
        updated_task = response.json()
        print(f"Updated task: {updated_task['title']}, version: {updated_task['version']}")
        assert response.status_code == 200
        assert updated_task["title"] == "Updated Task 1"
        assert updated_task["version"] == task["version"] + 1

        # Move task to different column
        print("\n9. Moving task to different column...")
        move_data = {
            "column_id": column_ids[1],  # Move to "In Progress"
            "order": 1000.0,
            "version": updated_task["version"],
        }
        response = await client.put(f"/api/tasks/{task_id}/move", json=move_data)
        print(f"Status: {response.status_code}")
        moved_task = response.json()
        print(f"Moved task to column: {moved_task['column_id']}")
        assert response.status_code == 200
        assert moved_task["column_id"] == column_ids[1]

        # Test optimistic locking (version conflict)
        print("\n10. Testing optimistic locking (should fail)...")
        old_version_data = {
            "title": "Should Fail",
            "version": moved_task["version"] - 1,  # Old version
        }
        response = await client.put(f"/api/tasks/{task_id}", json=old_version_data)
        print(f"Status: {response.status_code}")
        assert response.status_code == 409
        print("Optimistic locking working correctly (409 Conflict)")

        # Update column
        print("\n11. Updating a column...")
        column_id = column_ids[0]
        column_update = {"name": "Backlog (Updated)", "wip_limit": 5}
        response = await client.put(f"/api/columns/{column_id}", json=column_update)
        print(f"Status: {response.status_code}")
        updated_column = response.json()
        print(f"Updated column: {updated_column['name']}")
        assert response.status_code == 200

        # Delete a task
        print("\n12. Deleting a task...")
        response = await client.delete(f"/api/tasks/{task_ids[1]}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 204
        print("Task deleted successfully")

        # Delete a column
        print("\n13. Deleting a column...")
        response = await client.delete(f"/api/columns/{column_ids[2]}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 204
        print("Column deleted successfully")

        # Delete board
        print("\n14. Deleting board...")
        response = await client.delete(f"/api/boards/{board_id}")
        print(f"Status: {response.status_code}")
        assert response.status_code == 204
        print("Board deleted successfully")

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)


if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:8000")
    print("Start with: docker compose up -d")
    print()
    asyncio.run(test_api())
