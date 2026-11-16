def test_register_and_login_flow(client):
    # Register user
    reg_payload = {
        "name": "Test Editor",
        "email": "editor@clipforge.ai",
        "password": "password123"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "editor@clipforge.ai"
    token = data["access_token"]

    # Duplicate register should fail
    dup_res = client.post("/api/auth/register", json=reg_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["detail"]["error"]["code"] == "USER_ALREADY_EXISTS"

    # Login with valid credentials
    login_payload = {
        "email": "editor@clipforge.ai",
        "password": "password123"
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Login with wrong password
    bad_login = {
        "email": "editor@clipforge.ai",
        "password": "wrongpassword"
    }
    bad_res = client.post("/api/auth/login", json=bad_login)
    assert bad_res.status_code == 401

    # Get current user profile with token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Test Editor"

    # Unauthorized request without token
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401
