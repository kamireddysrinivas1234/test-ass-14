import importlib
from fastapi.testclient import TestClient

def make_client():
    # Import after DATABASE_URL is set by conftest fixture
    from app import main
    importlib.reload(main)
    return TestClient(main.app)

def login(client: TestClient, username: str, password: str) -> str:
    resp = client.post(
        "/users/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_root_loads():
    client = make_client()
    r = client.get("/")
    assert r.status_code == 200
    assert "FastAPI Calculator" in r.text

def test_demo_login_and_factory_paths():
    client = make_client()
    token = login(client, "demo", "Test123!")
    headers = {"Authorization": f"Bearer {token}"}

    # exercise factory ops: add/sub/mul/div
    for payload, expected in [
        ({"type":"add","a":2,"b":3}, 5),
        ({"type":"sub","a":10,"b":4}, 6),
        ({"type":"mul","a":3,"b":7}, 21),
        ({"type":"div","a":8,"b":2}, 4),
    ]:
        r = client.post("/calculations/", json=payload, headers=headers)
        assert r.status_code == 201
        assert r.json()["result"] == expected

def test_register_login_and_bread_full_cycle():
    client = make_client()

    r = client.post("/users/register", json={"username":"student","email":"student@example.com","password":"Pass123!"})
    assert r.status_code == 201
    # duplicates
    r2 = client.post("/users/register", json={"username":"student","email":"student2@example.com","password":"Pass123!"})
    assert r2.status_code == 400
    r3 = client.post("/users/register", json={"username":"student2","email":"student@example.com","password":"Pass123!"})
    assert r3.status_code == 400

    token = login(client, "student", "Pass123!")
    headers = {"Authorization": f"Bearer {token}"}

    # add
    r = client.post("/calculations/", json={"type":"add","a":2,"b":3}, headers=headers)
    assert r.status_code == 201
    cid = r.json()["id"]

    # browse
    r = client.get("/calculations/", headers=headers)
    assert r.status_code == 200
    assert any(x["id"] == cid for x in r.json())

    # read
    r = client.get(f"/calculations/{cid}", headers=headers)
    assert r.status_code == 200

    # edit
    r = client.put(f"/calculations/{cid}", json={"type":"mul","a":4,"b":5}, headers=headers)
    assert r.status_code == 200
    assert r.json()["result"] == 20

    # delete
    r = client.delete(f"/calculations/{cid}", headers=headers)
    assert r.status_code == 204

    # read again -> 404
    r = client.get(f"/calculations/{cid}", headers=headers)
    assert r.status_code == 404

def test_auth_and_ownership_protection():
    client = make_client()
    # no token
    r = client.get("/calculations/")
    assert r.status_code == 401

    # invalid token
    r = client.get("/calculations/", headers={"Authorization":"Bearer badtoken"})
    assert r.status_code == 401

    # create two users, ensure ownership enforced
    client.post("/users/register", json={"username":"u1","email":"u1@example.com","password":"Pass123!"})
    client.post("/users/register", json={"username":"u2","email":"u2@example.com","password":"Pass123!"})
    t1 = login(client, "u1", "Pass123!")
    t2 = login(client, "u2", "Pass123!")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    r = client.post("/calculations/", json={"type":"add","a":1,"b":1}, headers=h1)
    cid = r.json()["id"]

    # u2 cannot read/u2 gets 404
    r = client.get(f"/calculations/{cid}", headers=h2)
    assert r.status_code == 404

def test_divide_by_zero_validation():
    client = make_client()
    token = login(client, "demo", "Test123!")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/calculations/", json={"type":"div","a":10,"b":0}, headers=headers)
    assert r.status_code == 422

    # update guard
    r = client.post("/calculations/", json={"type":"add","a":10,"b":5}, headers=headers)
    cid = r.json()["id"]
    r = client.put(f"/calculations/{cid}", json={"type":"div","b":0}, headers=headers)
    assert r.status_code == 422
