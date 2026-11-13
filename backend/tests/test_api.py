def make_skill(client, headers, name, category_id):
    response = client.post("/api/skills", headers=headers, json={
        "name": name, "category_id": category_id, "description": f"Teaching {name}",
        "experience_level": "Intermediate",
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_auth_and_role_protection(client, create_account):
    user, headers = create_account("learner")
    profile = client.get("/api/auth/me", headers=headers).json()
    assert profile["username"] == "learner"
    assert profile["created_at"].endswith("+00:00")
    assert client.get("/api/users/me/profile").status_code == 401
    duplicate = client.post("/api/auth/register", json={
        "username": "learner", "email": "duplicate@example.com",
        "password": "secure-password-123",
    })
    assert duplicate.status_code == 409
    assert client.get("/api/admin/dashboard", headers=headers).status_code == 403
    admin = client.post("/api/auth/login", json={
        "email": "admin@example.com", "password": "secure-admin-password-123",
    })
    assert admin.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}
    assert client.get("/api/admin/dashboard", headers=admin_headers).status_code == 200
    assert user["id"] > 0


def test_deactivated_users_cannot_reuse_tokens_and_weak_password_is_rejected(client, create_account):
    user, headers = create_account("paused")
    admin = client.post("/api/auth/login", json={
        "email": "admin@example.com", "password": "secure-admin-password-123",
    }).json()
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}
    changed = client.patch(f"/api/admin/users/{user['id']}/status", headers=admin_headers, json={"is_active": False})
    assert changed.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    weak = client.post("/api/auth/register", json={
        "username": "weakuser", "email": "weak@example.com", "password": "short",
    })
    assert weak.status_code == 422


def test_profile_skills_posts_and_like_toggle(client, create_account):
    user, headers = create_account("maker")
    categories = client.get("/api/skills/categories").json()["items"]
    programming = next(item for item in categories if item["name"] == "Programming")
    skill = make_skill(client, headers, "Python", programming["id"])
    assert client.get("/api/users/me/teaching-skills", headers=headers).json()["total"] == 1
    updated = client.put("/api/users/me", headers=headers, json={"bio": "I teach Python"})
    assert updated.status_code == 200
    post = client.post("/api/posts", headers=headers, json={"content": "Learning together"})
    assert post.status_code == 201
    post_id = post.json()["id"]
    assert client.post(f"/api/posts/{post_id}/like", headers=headers).json()["liked"] is True
    assert client.post(f"/api/posts/{post_id}/like", headers=headers).json()["liked"] is False
    assert client.get("/api/posts", headers=headers).json()["total"] == 1
    same_like = client.post(f"/api/posts/{post_id}/like", headers=headers, json={"liked": True})
    assert same_like.json() == {"liked": True, "like_count": 1}
    assert client.post(f"/api/posts/{post_id}/like", headers=headers, json={"liked": True}).json()["like_count"] == 1
    assert client.get("/api/search", params={"q": "Python", "type": "skills"}).json()["total"] == 1
    assert client.delete(f"/api/skills/{skill['id']}", headers=headers).status_code == 204
    assert user["id"] > 0


def test_post_notifications_reports_and_read_state(client, create_account):
    owner, owner_headers = create_account("author")
    _, reader_headers = create_account("reader")
    post = client.post("/api/posts", headers=owner_headers, json={"content": "Community update"}).json()
    post_id = post["id"]
    assert client.post(f"/api/posts/{post_id}/like", headers=reader_headers, json={"liked": True}).status_code == 200
    comment = client.post(
        f"/api/posts/{post_id}/comments", headers=reader_headers, json={"content": "Helpful post"}
    )
    assert comment.status_code == 201
    report = client.post(
        f"/api/posts/{post_id}/report", headers=reader_headers, json={"reason": "Needs moderator review"}
    )
    assert report.status_code == 201
    items = client.get("/api/notifications", headers=owner_headers).json()["items"]
    assert {item["type"] for item in items} == {"post_like", "post_comment"}
    assert client.get("/api/notifications/unread-count", headers=owner_headers).json()["unread_count"] == 2
    assert client.patch(f"/api/notifications/{items[0]['id']}/read", headers=owner_headers).status_code == 200
    assert client.patch("/api/notifications/read-all", headers=owner_headers).status_code == 200
    assert client.get("/api/notifications/unread-count", headers=owner_headers).json()["unread_count"] == 0
    admin = client.post("/api/auth/login", json={
        "email": "admin@example.com", "password": "secure-admin-password-123",
    }).json()
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}
    reports = client.get("/api/admin/reports", headers=admin_headers).json()
    assert reports["total"] == 1
    assert client.patch(f"/api/admin/reports/{report.json()['id']}", headers=admin_headers,
                        json={"status": "resolved"}).json()["status"] == "resolved"


def test_exchange_duration_repeat_rule_and_private_reads(client, create_account):
    a, ah = create_account("alice")
    b, bh = create_account("bob")
    c, ch = create_account("outsider")
    categories = client.get("/api/skills/categories").json()["items"]
    programming = next(item for item in categories if item["name"] == "Programming")
    design = next(item for item in categories if item["name"] == "UI/UX Design")
    a_skill = make_skill(client, ah, "Python", programming["id"])
    b_skill = make_skill(client, bh, "Product design", design["id"])

    def request(headers, sender_id, offered_id, receiver_id, requested_id):
        return client.post("/api/exchanges/requests", headers=headers, json={
            "receiver_id": receiver_id, "offered_skill_id": offered_id,
            "requested_skill_id": requested_id, "duration_days": 10,
        })

    self_exchange = request(ah, a["id"], a_skill["id"], a["id"], a_skill["id"])
    assert self_exchange.status_code == 400
    first = request(ah, a["id"], a_skill["id"], b["id"], b_skill["id"])
    assert first.status_code == 201, first.text
    request_id = first.json()["id"]
    reverse_duplicate = request(bh, b["id"], b_skill["id"], a["id"], a_skill["id"])
    assert reverse_duplicate.status_code == 409
    assert client.post(f"/api/exchanges/requests/{request_id}/accept", headers=ah).status_code == 409
    counter = client.post(f"/api/exchanges/requests/{request_id}/counter", headers=bh, json={"duration_days": 12})
    assert counter.status_code == 200
    accepted = client.post(f"/api/exchanges/requests/{request_id}/accept", headers=ah)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["duration_days"] == 12
    exchange_id = accepted.json()["id"]
    assert client.get(f"/api/exchanges/{exchange_id}", headers=ch).status_code == 404
    assert client.post(f"/api/exchanges/{exchange_id}/complete", headers=ah).json()["status"] == "completed"

    repeat = request(bh, b["id"], b_skill["id"], a["id"], a_skill["id"])
    assert repeat.status_code == 201, repeat.text
    second = client.post(f"/api/exchanges/requests/{repeat.json()['id']}/accept", headers=ah)
    assert second.status_code == 200, second.text
    assert second.json()["cycle_number"] == 2
    client.post(f"/api/exchanges/{second.json()['id']}/complete", headers=bh)
    third = request(ah, a["id"], a_skill["id"], b["id"], b_skill["id"])
    assert third.status_code == 409
    assert client.get("/api/exchanges/history", headers=ah).json()["total"] == 2
    assert client.get("/api/notifications", headers=ch).json()["total"] == 0


def test_upload_rejects_spoofed_content_and_non_owner_edits(client, create_account):
    _, owner_headers = create_account("owner")
    _, other_headers = create_account("visitor")
    post = client.post("/api/posts", headers=owner_headers, json={"content": "Original"})
    post_id = post.json()["id"]
    changed = client.put(f"/api/posts/{post_id}", headers=other_headers, json={"content": "Hijacked"})
    assert changed.status_code == 404
    spoofed = client.post(
        f"/api/posts/{post_id}/media", headers=owner_headers,
        files={"file": ("image.png", b"not a png", "image/png")},
    )
    assert spoofed.status_code == 400
    wrong_extension = client.post(
        f"/api/posts/{post_id}/media", headers=owner_headers,
        files={"file": ("image.gif", b"GIF89a", "image/gif")},
    )
    assert wrong_extension.status_code == 400
