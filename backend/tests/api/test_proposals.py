import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db


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


def test_create_proposal(client, sample_contact):
    """Test creating a proposal via API."""
    response = client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Website Redesign",
            "description": "Complete website overhaul",
            "value": "15000.00",
            "status": "draft"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["contact_id"] == sample_contact["id"]
    assert data["title"] == "Website Redesign"
    assert data["value"] == "15000.00"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data


def test_create_proposal_minimal(client, sample_contact):
    """Test creating a proposal with minimal fields."""
    response = client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Basic Proposal"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert data["value"] is None


def test_create_proposal_invalid_contact(client):
    """Test creating a proposal with non-existent contact."""
    response = client.post(
        "/api/proposals/",
        json={
            "contact_id": 99999,
            "title": "Test Proposal"
        }
    )
    
    assert response.status_code == 404
    assert "Contact not found" in response.json()["detail"]


def test_get_proposal(client, sample_contact):
    """Test getting a proposal by ID."""
    # Create proposal
    create_response = client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Test Proposal"
        }
    )
    proposal_id = create_response.json()["id"]
    
    # Get proposal
    response = client.get(f"/api/proposals/{proposal_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == proposal_id
    assert data["title"] == "Test Proposal"


def test_get_proposal_not_found(client):
    """Test getting a non-existent proposal."""
    response = client.get("/api/proposals/99999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_proposals(client, sample_contact):
    """Test listing proposals."""
    # Create multiple proposals
    for i in range(5):
        client.post(
            "/api/proposals/",
            json={
                "contact_id": sample_contact["id"],
                "title": f"Proposal {i}"
            }
        )
    
    response = client.get("/api/proposals/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["page_size"] == 100


def test_list_proposals_pagination(client, sample_contact):
    """Test listing proposals with pagination."""
    # Create 5 proposals
    for i in range(5):
        client.post(
            "/api/proposals/",
            json={
                "contact_id": sample_contact["id"],
                "title": f"Proposal {i}"
            }
        )
    
    # Get first page
    response = client.get("/api/proposals/?skip=0&limit=3")
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    
    # Get second page
    response = client.get("/api/proposals/?skip=3&limit=3")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 2


def test_list_proposals_filter_by_contact(client):
    """Test filtering proposals by contact."""
    # Create two contacts
    contact1 = client.post(
        "/api/contacts/",
        json={"first_name": "Alice", "last_name": "Smith"}
    ).json()
    contact2 = client.post(
        "/api/contacts/",
        json={"first_name": "Bob", "last_name": "Jones"}
    ).json()
    
    # Create proposals for both
    client.post(
        "/api/proposals/",
        json={
            "contact_id": contact1["id"],
            "title": "Contact 1 - Proposal 1"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": contact1["id"],
            "title": "Contact 1 - Proposal 2"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": contact2["id"],
            "title": "Contact 2 - Proposal"
        }
    )
    
    response = client.get(f"/api/proposals/?contact_id={contact1['id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_list_proposals_filter_by_status(client, sample_contact):
    """Test filtering proposals by status."""
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Draft Proposal",
            "status": "draft"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Submitted Proposal",
            "status": "submitted"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Won Proposal",
            "status": "won"
        }
    )
    
    response = client.get("/api/proposals/?status=draft")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Draft Proposal"


def test_list_proposals_filter_by_value_range(client, sample_contact):
    """Test filtering proposals by value range."""
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Small Project",
            "value": "5000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Medium Project",
            "value": "15000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Large Project",
            "value": "50000.00"
        }
    )
    
    # Get proposals between 10k and 30k
    response = client.get("/api/proposals/?min_value=10000&max_value=30000")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Medium Project"


def test_update_proposal(client, sample_contact):
    """Test updating a proposal."""
    # Create proposal
    create_response = client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Original Title",
            "status": "draft",
            "value": "10000.00"
        }
    )
    proposal_id = create_response.json()["id"]
    
    # Update proposal
    response = client.put(
        f"/api/proposals/{proposal_id}",
        json={
            "title": "Updated Title",
            "status": "submitted",
            "value": "12000.00"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "submitted"
    assert data["value"] == "12000.00"


def test_update_proposal_not_found(client):
    """Test updating a non-existent proposal."""
    response = client.put(
        "/api/proposals/99999",
        json={"title": "New Title"}
    )
    
    assert response.status_code == 404


def test_delete_proposal(client, sample_contact):
    """Test deleting a proposal."""
    # Create proposal
    create_response = client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Test Proposal"
        }
    )
    proposal_id = create_response.json()["id"]
    
    # Delete proposal
    response = client.delete(f"/api/proposals/{proposal_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/proposals/{proposal_id}")
    assert get_response.status_code == 404


def test_delete_proposal_not_found(client):
    """Test deleting a non-existent proposal."""
    response = client.delete("/api/proposals/99999")
    
    assert response.status_code == 404


def test_get_contact_proposals(client, sample_contact):
    """Test getting all proposals for a contact."""
    # Create proposals
    for i in range(3):
        client.post(
            "/api/proposals/",
            json={
                "contact_id": sample_contact["id"],
                "title": f"Proposal {i}"
            }
        )
    
    response = client.get(f"/api/proposals/contact/{sample_contact['id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(p["contact_id"] == sample_contact["id"] for p in data)


def test_get_contact_proposals_not_found(client):
    """Test getting proposals for non-existent contact."""
    response = client.get("/api/proposals/contact/99999")
    
    assert response.status_code == 404


def test_get_expired_proposals(client, sample_contact):
    """Test getting expired proposals."""
    now = datetime.now(timezone.utc)
    
    # Create expired proposal
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Expired Proposal",
            "status": "submitted",
            "expires_at": (now - timedelta(days=1)).isoformat()
        }
    )
    
    # Create active proposal
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Active Proposal",
            "status": "submitted",
            "expires_at": (now + timedelta(days=30)).isoformat()
        }
    )
    
    # Create expired but won proposal (should not be included)
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Expired Won",
            "status": "won",
            "expires_at": (now - timedelta(days=1)).isoformat()
        }
    )
    
    response = client.get("/api/proposals/expired")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Expired Proposal"


def test_get_proposal_stats(client, sample_contact):
    """Test getting proposal statistics."""
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Draft 1",
            "status": "draft",
            "value": "5000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Draft 2",
            "status": "draft",
            "value": "7000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Won",
            "status": "won",
            "value": "15000.00"
        }
    )
    
    response = client.get("/api/proposals/stats/by-status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 3
    assert data["total_value"] == 27000.00
    assert data["by_status"]["draft"]["count"] == 2
    assert data["by_status"]["draft"]["total_value"] == 12000.00
    assert data["by_status"]["won"]["count"] == 1
    assert data["by_status"]["won"]["total_value"] == 15000.00


def test_get_proposal_stats_filtered_by_contact(client):
    """Test getting proposal statistics for specific contact."""
    contact1 = client.post(
        "/api/contacts/",
        json={"first_name": "Alice", "last_name": "Smith"}
    ).json()
    contact2 = client.post(
        "/api/contacts/",
        json={"first_name": "Bob", "last_name": "Jones"}
    ).json()
    
    # Create proposals for contact1
    client.post(
        "/api/proposals/",
        json={
            "contact_id": contact1["id"],
            "title": "Draft",
            "status": "draft",
            "value": "10000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": contact1["id"],
            "title": "Won",
            "status": "won",
            "value": "20000.00"
        }
    )
    
    # Create proposal for contact2
    client.post(
        "/api/proposals/",
        json={
            "contact_id": contact2["id"],
            "title": "Draft",
            "status": "draft",
            "value": "5000.00"
        }
    )
    
    response = client.get(f"/api/proposals/stats/by-status?contact_id={contact1['id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert data["total_value"] == 30000.00
    assert data["by_status"]["draft"]["count"] == 1
    assert data["by_status"]["draft"]["total_value"] == 10000.00


def test_combined_filters(client, sample_contact):
    """Test combining multiple filters."""
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Draft Small",
            "status": "draft",
            "value": "5000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Draft Large",
            "status": "draft",
            "value": "50000.00"
        }
    )
    client.post(
        "/api/proposals/",
        json={
            "contact_id": sample_contact["id"],
            "title": "Won Large",
            "status": "won",
            "value": "50000.00"
        }
    )
    
    # Filter by status AND value range
    response = client.get(
        f"/api/proposals/?contact_id={sample_contact['id']}&status=draft&min_value=10000"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Draft Large"