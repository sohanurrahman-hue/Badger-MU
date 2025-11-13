"""
Tests for SCIM 2.0 endpoints
"""
import pytest
from unittest.mock import patch
from backend.db.models import User


class TestSCIMUsers:
    """Test SCIM Users endpoint"""
    
    @pytest.fixture
    def auth_headers(self, mock_entra_token):
        """Auth headers for SCIM requests"""
        return {"Authorization": f"Bearer {mock_entra_token}"}
    
    def test_list_users_unauthorized(self, client):
        """Test listing users without authentication"""
        response = client.get("/scim/v2/Users")
        assert response.status_code == 401
    
    def test_list_users_success(self, client, db, admin_user, auth_headers):
        """Test listing users with admin access"""
        # Create test users
        user1 = User(email="user1@example.com", name="User 1", is_active=True)
        user2 = User(email="user2@example.com", name="User 2", is_active=True)
        db.add(user1)
        db.add(user2)
        db.commit()
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.get("/scim/v2/Users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert data["totalResults"] >= 2
    
    def test_create_user_success(self, client, db, admin_user, auth_headers):
        """Test creating a user via SCIM"""
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "newuser@example.com",
            "name": {
                "formatted": "New User",
                "givenName": "New",
                "familyName": "User"
            },
            "emails": [
                {"value": "newuser@example.com", "primary": True}
            ],
            "active": True
        }
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.post("/scim/v2/Users", json=user_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["userName"] == "newuser@example.com"
        assert "id" in data
    
    def test_create_user_duplicate(self, client, db, admin_user, auth_headers):
        """Test creating a duplicate user"""
        # Create existing user
        existing_user = User(email="existing@example.com", name="Existing User")
        db.add(existing_user)
        db.commit()
        
        user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "existing@example.com",
            "emails": [{"value": "existing@example.com"}],
            "active": True
        }
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.post("/scim/v2/Users", json=user_data, headers=auth_headers)
        
        assert response.status_code == 409
    
    def test_get_user_success(self, client, db, admin_user, auth_headers):
        """Test getting a specific user"""
        user = User(email="testuser@example.com", name="Test User", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.get(f"/scim/v2/Users/{user.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["userName"] == "testuser@example.com"
    
    def test_get_user_not_found(self, client, admin_user, auth_headers):
        """Test getting a non-existent user"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.get(f"/scim/v2/Users/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_patch_user_deactivate(self, client, db, admin_user, auth_headers):
        """Test deactivating a user via PATCH"""
        user = User(email="active@example.com", name="Active User", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "active",
                    "value": False
                }
            ]
        }
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.patch(f"/scim/v2/Users/{user.id}", json=patch_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
    
    def test_delete_user_success(self, client, db, admin_user, auth_headers):
        """Test soft-deleting a user"""
        user = User(email="delete@example.com", name="Delete User", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.delete(f"/scim/v2/Users/{user.id}", headers=auth_headers)
        
        assert response.status_code == 204


class TestSCIMGroups:
    """Test SCIM Groups endpoint"""
    
    @pytest.fixture
    def auth_headers(self, mock_entra_token):
        """Auth headers for SCIM requests"""
        return {"Authorization": f"Bearer {mock_entra_token}"}
    
    def test_list_groups_success(self, client, admin_user, auth_headers):
        """Test listing groups"""
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.get("/scim/v2/Groups", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert data["totalResults"] >= 1  # Default "Issuers" group exists
    
    def test_create_group_success(self, client, admin_user, auth_headers):
        """Test creating a group"""
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Test Group",
            "members": []
        }
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.post("/scim/v2/Groups", json=group_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["displayName"] == "Test Group"
        assert "id" in data
    
    def test_patch_group_add_member(self, client, admin_user, auth_headers):
        """Test adding a member to a group"""
        # First create a group
        group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": "Test Group",
            "members": []
        }
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                create_response = client.post("/scim/v2/Groups", json=group_data, headers=auth_headers)
                group_id = create_response.json()["id"]
        
        # Now add a member
        patch_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "members",
                    "value": [
                        {
                            "value": "user-id-123",
                            "display": "Test User"
                        }
                    ]
                }
            ]
        }
        
        with patch('backend.auth.middleware.get_current_user', return_value=admin_user):
            with patch('backend.auth.middleware.get_current_user_groups', return_value=admin_user["groups"]):
                response = client.patch(f"/scim/v2/Groups/{group_id}", json=patch_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["members"]) == 1
        assert data["members"][0]["value"] == "user-id-123"
    
    def test_get_service_provider_config(self, client):
        """Test SCIM service provider configuration endpoint"""
        response = client.get("/scim/v2/ServiceProviderConfig")
        assert response.status_code == 200
        data = response.json()
        assert "patch" in data
        assert data["patch"]["supported"] is True

