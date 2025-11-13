"""
Tests for authentication module
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.auth.sso import EntraIDAuth
from backend.auth.middleware import AuthMiddleware


class TestEntraIDAuth:
    """Test Entra ID authentication"""
    
    def test_get_auth_url(self):
        """Test auth URL generation"""
        auth = EntraIDAuth()
        url = auth.get_auth_url()
        
        assert "login.microsoftonline.com" in url
        assert "oauth2/v2.0/authorize" in url
        assert auth.client_id in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        """Test successful token exchange"""
        auth = EntraIDAuth()
        
        mock_result = {
            "access_token": "mock_access_token",
            "expires_in": 3600,
            "refresh_token": "mock_refresh_token",
            "id_token": "mock_id_token"
        }
        
        with patch.object(auth.app, 'acquire_token_by_authorization_code', return_value=mock_result):
            result = await auth.exchange_code_for_token("mock_code")
            
            assert result["access_token"] == "mock_access_token"
            assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_error(self):
        """Test token exchange error handling"""
        auth = EntraIDAuth()
        
        mock_result = {
            "error": "invalid_grant",
            "error_description": "Invalid authorization code"
        }
        
        with patch.object(auth.app, 'acquire_token_by_authorization_code', return_value=mock_result):
            with pytest.raises(Exception):
                await auth.exchange_code_for_token("invalid_code")
    
    def test_validate_token_valid(self):
        """Test token validation with valid token"""
        auth = EntraIDAuth()
        
        mock_payload = {
            "oid": "user-id",
            "preferred_username": "user@example.com",
            "name": "Test User",
            "groups": ["group1", "group2"]
        }
        
        with patch('jwt.decode', return_value=mock_payload):
            with patch.object(auth.jwks_client, 'get_signing_key_from_jwt'):
                payload = auth.validate_token("mock.jwt.token")
                
                assert payload["oid"] == "user-id"
                assert payload["preferred_username"] == "user@example.com"
    
    def test_validate_token_expired(self):
        """Test token validation with expired token"""
        auth = EntraIDAuth()
        
        import jwt
        with patch('jwt.decode', side_effect=jwt.ExpiredSignatureError):
            with pytest.raises(Exception) as exc_info:
                auth.validate_token("expired.jwt.token")
    
    def test_check_admin_access_allowed(self):
        """Test admin access check with admin group"""
        auth = EntraIDAuth()
        auth.admin_groups = ["Badge Admins", "Platform Admins"]
        
        user_groups = ["Issuers", "Badge Admins"]
        assert auth.check_admin_access(user_groups) is True
    
    def test_check_admin_access_denied(self):
        """Test admin access check without admin group"""
        auth = EntraIDAuth()
        auth.admin_groups = ["Badge Admins", "Platform Admins"]
        
        user_groups = ["Issuers", "Regular Users"]
        assert auth.check_admin_access(user_groups) is False
    
    def test_check_issuer_access_allowed(self):
        """Test issuer access check with issuer group"""
        auth = EntraIDAuth()
        auth.issuer_groups = ["Issuers"]
        
        user_groups = ["Issuers"]
        assert auth.check_issuer_access(user_groups) is True
    
    def test_check_issuer_access_denied(self):
        """Test issuer access check without issuer group"""
        auth = EntraIDAuth()
        auth.issuer_groups = ["Issuers"]
        
        user_groups = ["Regular Users"]
        assert auth.check_issuer_access(user_groups) is False


class TestAuthMiddleware:
    """Test authentication middleware"""
    
    def test_public_routes_allowed(self, client):
        """Test that public routes don't require authentication"""
        response = client.get("/")
        assert response.status_code == 200
        
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_protected_route_no_auth(self, client):
        """Test that protected routes require authentication"""
        response = client.get("/api/achievements/")
        assert response.status_code == 401
        assert "Authorization" in response.json()["detail"]
    
    def test_protected_route_with_auth(self, client, mock_user):
        """Test protected route with valid authentication"""
        with patch('backend.auth.sso.entra_auth.validate_token', return_value=mock_user):
            response = client.get(
                "/api/achievements/",
                headers={"Authorization": "Bearer mock.jwt.token"}
            )
            # May return 200 or other status depending on implementation
            assert response.status_code != 401
    
    def test_admin_route_requires_admin_group(self, client, issuer_user):
        """Test that admin routes require admin group membership"""
        with patch('backend.auth.sso.entra_auth.validate_token', return_value=issuer_user):
            with patch('backend.auth.sso.entra_auth.extract_groups_from_token', return_value=["Issuers"]):
                response = client.get(
                    "/scim/v2/Users",
                    headers={"Authorization": "Bearer mock.jwt.token"}
                )
                assert response.status_code == 403

