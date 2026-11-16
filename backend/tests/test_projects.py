def test_projects_crud_flow(client):
    # 1. Register test user
    reg = client.post("/api/auth/register", json={
        "name": "Project Creator",
        "email": "creator@clipforge.ai",
        "password": "secretpassword"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List projects (initially empty)
    list_res = client.get("/api/projects", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json() == []

    # 3. Create project
    create_res = client.post("/api/projects", json={
        "title": "My First AI Video",
        "description": "YouTube Shorts draft"
    }, headers=headers)
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]
    assert create_res.json()["title"] == "My First AI Video"
    assert create_res.json()["status"] == "created"

    # 4. Get project details
    get_res = client.get(f"/api/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

    # 5. Check transcript endpoint before processing
    trans_res = client.get(f"/api/projects/{project_id}/transcript", headers=headers)
    assert trans_res.status_code == 200
    assert trans_res.json()["status"] == "pending"

    # 6. Delete project
    del_res = client.delete(f"/api/projects/{project_id}", headers=headers)
    assert del_res.status_code == 204

    # 7. Confirm deletion
    not_found = client.get(f"/api/projects/{project_id}", headers=headers)
    assert not_found.status_code == 404
