import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models.contact import ContactStatus


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


def test_create_contact(client):
    """Test creating a contact via API."""
    response = client.post(
        "/api/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "company": "Acme Corp",
            "tags": ["vip", "tech"]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john@example.com"
    assert data["status"] == "lead"
    assert data["tags"] == ["vip", "tech"]
    assert "id" in data
    assert "created_at" in data


def test_create_contact_minimal(client):
    """Test creating a contact with minimal fields."""
    response = client.post(
        "/api/contacts/",
        json={
            "first_name": "Jane",
            "last_name": "Smith"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["tags"] == []


def test_create_contact_duplicate_email(client):
    """Test creating a contact with duplicate email."""
    client.post(
        "/api/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "duplicate@example.com"
        }
    )
    
    response = client.post(
        "/api/contacts/",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "duplicate@example.com"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_create_contact_invalid_email(client):
    """Test creating a contact with invalid email."""
    response = client.post(
        "/api/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "not-an-email"
        }
    )
    
    assert response.status_code == 422


def test_get_contact(client):
    """Test getting a contact by ID."""
    # Create contact
    create_response = client.post(
        "/api/contacts/",
        json={"first_name": "John", "last_name": "Doe"}
    )
    contact_id = create_response.json()["id"]
    
    # Get contact
    response = client.get(f"/api/contacts/{contact_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact_id
    assert data["first_name"] == "John"


def test_get_contact_not_found(client):
    """Test getting a non-existent contact."""
    response = client.get("/api/contacts/99999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_contacts(client):
    """Test listing contacts."""
    # Create multiple contacts
    for i in range(5):
        client.post(
            "/api/contacts/",
            json={"first_name": f"User{i}", "last_name": "Test"}
        )
    
    response = client.get("/api/contacts/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 100


def test_list_contacts_pagination(client):
    """Test listing contacts with pagination."""
    # Create 5 contacts
    for i in range(5):
        client.post(
            "/api/contacts/",
            json={"first_name": f"User{i}", "last_name": "Test"}
        )
    
    # Get first page
    response = client.get("/api/contacts/?skip=0&limit=3")
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    
    # Get second page
    response = client.get("/api/contacts/?skip=3&limit=3")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2


def test_list_contacts_filter_by_status(client):
    """Test filtering contacts by status."""
    client.post(
        "/api/contacts/",
        json={"first_name": "Lead", "last_name": "User", "status": "lead"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Client", "last_name": "User", "status": "client"}
    )
    
    response = client.get("/api/contacts/?status=lead")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["first_name"] == "Lead"


def test_list_contacts_search(client):
    """Test searching contacts."""
    client.post(
        "/api/contacts/",
        json={"first_name": "Alice", "last_name": "Johnson", "email": "alice@example.com"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Bob", "last_name": "Smith", "company": "Alice Corp"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Charlie", "last_name": "Brown"}
    )
    
    response = client.get("/api/contacts/?search=alice")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_contacts_filter_by_tags(client):
    """Test filtering contacts by tags."""
    client.post(
        "/api/contacts/",
        json={"first_name": "VIP", "last_name": "User", "tags": ["vip", "tech"]}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Tech", "last_name": "User", "tags": ["tech"]}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Normal", "last_name": "User", "tags": []}
    )
    
    response = client.get("/api/contacts/?tags=vip")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["first_name"] == "VIP"


def test_update_contact(client):
    """Test updating a contact."""
    # Create contact
    create_response = client.post(
        "/api/contacts/",
        json={"first_name": "John", "last_name": "Doe", "status": "lead"}
    )
    contact_id = create_response.json()["id"]
    
    # Update contact
    response = client.put(
        f"/api/contacts/{contact_id}",
        json={"first_name": "Jane", "status": "client", "company": "New Corp"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"  # Unchanged
    assert data["status"] == "client"
    assert data["company"] == "New Corp"


def test_update_contact_not_found(client):
    """Test updating a non-existent contact."""
    response = client.put(
        "/api/contacts/99999",
        json={"first_name": "Jane"}
    )
    
    assert response.status_code == 404


def test_update_contact_duplicate_email(client):
    """Test updating a contact with duplicate email."""
    # Create two contacts
    client.post(
        "/api/contacts/",
        json={"first_name": "John", "last_name": "Doe", "email": "john@example.com"}
    )
    create_response = client.post(
        "/api/contacts/",
        json={"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}
    )
    contact_id = create_response.json()["id"]
    
    # Try to update with existing email
    response = client.put(
        f"/api/contacts/{contact_id}",
        json={"email": "john@example.com"}
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_delete_contact(client):
    """Test deleting a contact."""
    # Create contact
    create_response = client.post(
        "/api/contacts/",
        json={"first_name": "John", "last_name": "Doe"}
    )
    contact_id = create_response.json()["id"]
    
    # Delete contact
    response = client.delete(f"/api/contacts/{contact_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/contacts/{contact_id}")
    assert get_response.status_code == 404


def test_delete_contact_not_found(client):
    """Test deleting a non-existent contact."""
    response = client.delete("/api/contacts/99999")
    
    assert response.status_code == 404


def test_search_contacts(client):
    """Test search endpoint."""
    client.post(
        "/api/contacts/",
        json={"first_name": "Alice", "last_name": "Anderson"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Bob", "last_name": "Alison"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Charlie", "last_name": "Brown"}
    )
    
    response = client.get("/api/contacts/search/ali")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_contact_stats(client):
    """Test getting contact statistics."""
    client.post(
        "/api/contacts/",
        json={"first_name": "Lead1", "last_name": "User", "status": "lead"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Lead2", "last_name": "User", "status": "lead"}
    )
    client.post(
        "/api/contacts/",
        json={"first_name": "Client", "last_name": "User", "status": "client"}
    )
    
    response = client.get("/api/contacts/stats/by-status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["by_status"]["lead"] == 2
    assert data["by_status"]["client"] == 1


def test_combined_filters(client):
    """Test combining multiple filters."""
    client.post(
        "/api/contacts/",
        json={
            "first_name": "Alice",
            "last_name": "VIP",
            "status": "client",
            "tags": ["vip"]
        }
    )
    client.post(
        "/api/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "VIP",
            "status": "lead",
            "tags": ["vip"]
        }
    )
    
    response = client.get("/api/contacts/?status=client&tags=vip")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["first_name"] == "Alice"