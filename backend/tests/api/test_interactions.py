import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models.interaction import InteractionType


@pytest.fixture
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_contact(client):
    """Create a sample contact for testing."""
    response = client.post(
        "/api/contacts/",
        json={"first_name": "John", "last_name": "Doe"}
    )
    return response.json()


def test_create_interaction(client, sample_contact):
    """Test creating an interaction via API."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Initial call to discuss project",
            "outcome": "Interested in proposal"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["contact_id"] == sample_contact["id"]
    assert data["type"] == "call"
    assert data["summary"] == "Initial call to discuss project"
    assert data["outcome"] == "Interested in proposal"
    assert "id" in data
    assert "created_at" in data


def test_create_interaction_minimal(client, sample_contact):
    """Test creating an interaction with minimal fields."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": occurred_at,
            "summary": "Quick note"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "note"


def test_create_interaction_invalid_contact(client):
    """Test creating an interaction with non-existent contact."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/interactions/",
        json={
            "contact_id": 99999,
            "occurred_at": occurred_at,
            "summary": "Test"
        }
    )
    
    assert response.status_code == 404
    assert "Contact not found" in response.json()["detail"]


def test_get_interaction(client, sample_contact):
    """Test getting an interaction by ID."""
    # Create interaction
    occurred_at = datetime.now(timezone.utc).isoformat()
    create_response = client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": occurred_at,
            "summary": "Test interaction"
        }
    )
    interaction_id = create_response.json()["id"]
    
    # Get interaction
    response = client.get(f"/api/interactions/{interaction_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == interaction_id
    assert data["summary"] == "Test interaction"


def test_get_interaction_not_found(client):
    """Test getting a non-existent interaction."""
    response = client.get("/api/interactions/99999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_interactions(client, sample_contact):
    """Test listing interactions."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    # Create multiple interactions
    for i in range(5):
        client.post(
            "/api/interactions/",
            json={
                "contact_id": sample_contact["id"],
                "occurred_at": occurred_at,
                "summary": f"Interaction {i}"
            }
        )
    
    response = client.get("/api/interactions/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 100


def test_list_interactions_pagination(client, sample_contact):
    """Test listing interactions with pagination."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    # Create 5 interactions
    for i in range(5):
        client.post(
            "/api/interactions/",
            json={
                "contact_id": sample_contact["id"],
                "occurred_at": occurred_at,
                "summary": f"Interaction {i}"
            }
        )
    
    # Get first page
    response = client.get("/api/interactions/?skip=0&limit=3")
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    
    # Get second page
    response = client.get("/api/interactions/?skip=3&limit=3")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2


def test_list_interactions_filter_by_contact(client):
    """Test filtering interactions by contact."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    # Create two contacts
    contact1 = client.post(
        "/api/contacts/",
        json={"first_name": "Alice", "last_name": "Smith"}
    ).json()
    contact2 = client.post(
        "/api/contacts/",
        json={"first_name": "Bob", "last_name": "Jones"}
    ).json()
    
    # Create interactions for both
    client.post(
        "/api/interactions/",
        json={
            "contact_id": contact1["id"],
            "occurred_at": occurred_at,
            "summary": "Contact 1 - Call 1"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": contact1["id"],
            "occurred_at": occurred_at,
            "summary": "Contact 1 - Call 2"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": contact2["id"],
            "occurred_at": occurred_at,
            "summary": "Contact 2 - Call"
        }
    )
    
    response = client.get(f"/api/interactions/?contact_id={contact1['id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_interactions_filter_by_type(client, sample_contact):
    """Test filtering interactions by type."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Call"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "email",
            "occurred_at": occurred_at,
            "summary": "Email"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Another call"
        }
    )
    
    response = client.get("/api/interactions/?interaction_type=call")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_interactions_filter_by_date_range(client, sample_contact):
    """Test filtering interactions by date range."""
    now = datetime.now(timezone.utc)
    
    # Create interactions at different times
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": (now - timedelta(days=10)).isoformat(),
            "summary": "Old interaction"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": (now - timedelta(days=3)).isoformat(),
            "summary": "Recent interaction"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": now.isoformat(),
            "summary": "Today interaction"
        }
    )
    
    # Get interactions from last 7 days
    start_date = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    response = client.get(f"/api/interactions/?start_date={start_date}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_update_interaction(client, sample_contact):
    """Test updating an interaction."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    # Create interaction
    create_response = client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "note",
            "occurred_at": occurred_at,
            "summary": "Original summary"
        }
    )
    interaction_id = create_response.json()["id"]
    
    # Update interaction
    response = client.put(
        f"/api/interactions/{interaction_id}",
        json={
            "type": "call",
            "summary": "Updated summary",
            "outcome": "Successful"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "call"
    assert data["summary"] == "Updated summary"
    assert data["outcome"] == "Successful"


def test_update_interaction_not_found(client):
    """Test updating a non-existent interaction."""
    response = client.put(
        "/api/interactions/99999",
        json={"summary": "New summary"}
    )
    
    assert response.status_code == 404


def test_delete_interaction(client, sample_contact):
    """Test deleting an interaction."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    # Create interaction
    create_response = client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": occurred_at,
            "summary": "Test interaction"
        }
    )
    interaction_id = create_response.json()["id"]
    
    # Delete interaction
    response = client.delete(f"/api/interactions/{interaction_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/interactions/{interaction_id}")
    assert get_response.status_code == 404


def test_delete_interaction_not_found(client):
    """Test deleting a non-existent interaction."""
    response = client.delete("/api/interactions/99999")
    
    assert response.status_code == 404


def test_get_contact_interactions(client, sample_contact):
    """Test getting all interactions for a contact."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    # Create interactions
    for i in range(3):
        client.post(
            "/api/interactions/",
            json={
                "contact_id": sample_contact["id"],
                "occurred_at": occurred_at,
                "summary": f"Interaction {i}"
            }
        )
    
    response = client.get(f"/api/interactions/contact/{sample_contact['id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(i["contact_id"] == sample_contact["id"] for i in data)


def test_get_contact_interactions_not_found(client):
    """Test getting interactions for non-existent contact."""
    response = client.get("/api/interactions/contact/99999")
    
    assert response.status_code == 404


def test_get_recent_interactions(client, sample_contact):
    """Test getting recent interactions."""
    now = datetime.now(timezone.utc)
    
    # Create interactions at different times
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": (now - timedelta(days=2)).isoformat(),
            "summary": "Recent"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "occurred_at": (now - timedelta(days=10)).isoformat(),
            "summary": "Old"
        }
    )
    
    # Get interactions from last 7 days
    response = client.get("/api/interactions/recent?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["summary"] == "Recent"


def test_get_interaction_stats(client, sample_contact):
    """Test getting interaction statistics."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Call 1"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Call 2"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "email",
            "occurred_at": occurred_at,
            "summary": "Email"
        }
    )
    
    response = client.get("/api/interactions/stats/by-type")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["by_type"]["call"] == 2
    assert data["by_type"]["email"] == 1


def test_get_interaction_stats_filtered_by_contact(client):
    """Test getting interaction statistics for specific contact."""
    occurred_at = datetime.now(timezone.utc).isoformat()
    
    contact1 = client.post(
        "/api/contacts/",
        json={"first_name": "Alice", "last_name": "Smith"}
    ).json()
    contact2 = client.post(
        "/api/contacts/",
        json={"first_name": "Bob", "last_name": "Jones"}
    ).json()
    
    # Create interactions for contact1
    client.post(
        "/api/interactions/",
        json={
            "contact_id": contact1["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Call"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": contact1["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Call 2"
        }
    )
    
    # Create interaction for contact2
    client.post(
        "/api/interactions/",
        json={
            "contact_id": contact2["id"],
            "type": "call",
            "occurred_at": occurred_at,
            "summary": "Call"
        }
    )
    
    response = client.get(f"/api/interactions/stats/by-type?contact_id={contact1['id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["by_type"]["call"] == 2


def test_combined_filters(client, sample_contact):
    """Test combining multiple filters."""
    now = datetime.now(timezone.utc)
    
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": (now - timedelta(days=2)).isoformat(),
            "summary": "Recent call"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "email",
            "occurred_at": (now - timedelta(days=2)).isoformat(),
            "summary": "Recent email"
        }
    )
    client.post(
        "/api/interactions/",
        json={
            "contact_id": sample_contact["id"],
            "type": "call",
            "occurred_at": (now - timedelta(days=10)).isoformat(),
            "summary": "Old call"
        }
    )
    
    # Filter by type AND date range
    start_date = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    response = client.get(
        f"/api/interactions/?contact_id={sample_contact['id']}&interaction_type=call&start_date={start_date}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["summary"] == "Recent call"