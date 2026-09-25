from instructor.dashboard import app, state


def test_dashboard_accepts_and_returns_team_state():
    state.clear()
    client = app.test_client()
    response = client.post(
        "/api/update",
        json={
            "team": "Test Team",
            "task": "env/goto_win",
            "step": 3,
            "max_steps": 20,
            "success": False,
            "cost_usd": 0.01,
        },
    )
    assert response.status_code == 200
    payload = client.get("/api/state").get_json()
    assert payload["Test Team"]["step"] == 3
    assert b"Baba Agent Tournament" in client.get("/").data

