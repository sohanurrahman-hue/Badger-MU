"""
Tests for badge baking functionality
"""
import pytest
import base64
import json
from backend.services.badge_service import BadgeBakingService


class TestBadgeBaking:
    """Test badge baking service"""
    
    @pytest.fixture
    def sample_png(self):
        """Sample PNG image (1x1 black pixel)"""
        # Minimal valid PNG
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return png_data
    
    @pytest.fixture
    def sample_svg(self):
        """Sample SVG image"""
        return """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
</svg>"""
    
    @pytest.fixture
    def credential_dict(self, sample_credential):
        """Sample credential as dict"""
        return sample_credential
    
    def test_bake_png_success(self, sample_png, credential_dict):
        """Test successful PNG baking"""
        service = BadgeBakingService()
        
        baked_png = service.bake_png(sample_png, credential_dict, overwrite=False)
        
        assert isinstance(baked_png, bytes)
        assert len(baked_png) > len(sample_png)  # Should be larger with credential
    
    def test_bake_png_overwrite_false_error(self, sample_png, credential_dict):
        """Test PNG baking with existing credential and overwrite=False"""
        service = BadgeBakingService()
        
        # Bake once
        baked_png = service.bake_png(sample_png, credential_dict, overwrite=False)
        
        # Try to bake again without overwrite
        with pytest.raises(ValueError) as exc_info:
            service.bake_png(baked_png, credential_dict, overwrite=False)
        
        assert "already exists" in str(exc_info.value)
    
    def test_bake_png_overwrite_true(self, sample_png, credential_dict):
        """Test PNG baking with overwrite=True"""
        service = BadgeBakingService()
        
        # Bake once
        baked_png = service.bake_png(sample_png, credential_dict, overwrite=False)
        
        # Bake again with different credential and overwrite=True
        new_credential = credential_dict.copy()
        new_credential["id"] = "https://example.com/credentials/new"
        
        rebaked_png = service.bake_png(baked_png, new_credential, overwrite=True)
        
        assert isinstance(rebaked_png, bytes)
    
    def test_extract_png_success(self, sample_png, credential_dict):
        """Test successful PNG extraction"""
        service = BadgeBakingService()
        
        # Bake credential
        baked_png = service.bake_png(sample_png, credential_dict, overwrite=False)
        
        # Extract credential
        extracted = service.extract_png(baked_png)
        
        assert extracted is not None
        assert extracted["id"] == credential_dict["id"]
        assert extracted["type"] == credential_dict["type"]
    
    def test_extract_png_not_found(self, sample_png):
        """Test PNG extraction when no credential exists"""
        service = BadgeBakingService()
        
        extracted = service.extract_png(sample_png)
        
        assert extracted is None
    
    def test_bake_svg_success(self, sample_svg, credential_dict):
        """Test successful SVG baking"""
        service = BadgeBakingService()
        
        baked_svg = service.bake_svg(sample_svg, credential_dict, overwrite=False)
        
        assert isinstance(baked_svg, str)
        assert "<openbadges:credential" in baked_svg
        assert "xmlns:openbadges" in baked_svg
    
    def test_bake_svg_overwrite_false_error(self, sample_svg, credential_dict):
        """Test SVG baking with existing credential and overwrite=False"""
        service = BadgeBakingService()
        
        # Bake once
        baked_svg = service.bake_svg(sample_svg, credential_dict, overwrite=False)
        
        # Try to bake again without overwrite
        with pytest.raises(ValueError) as exc_info:
            service.bake_svg(baked_svg, credential_dict, overwrite=False)
        
        assert "already exists" in str(exc_info.value)
    
    def test_bake_svg_overwrite_true(self, sample_svg, credential_dict):
        """Test SVG baking with overwrite=True"""
        service = BadgeBakingService()
        
        # Bake once
        baked_svg = service.bake_svg(sample_svg, credential_dict, overwrite=False)
        
        # Bake again with different credential
        new_credential = credential_dict.copy()
        new_credential["id"] = "https://example.com/credentials/new"
        
        rebaked_svg = service.bake_svg(baked_svg, new_credential, overwrite=True)
        
        assert isinstance(rebaked_svg, str)
        assert "<openbadges:credential" in rebaked_svg
    
    def test_extract_svg_success(self, sample_svg, credential_dict):
        """Test successful SVG extraction"""
        service = BadgeBakingService()
        
        # Bake credential
        baked_svg = service.bake_svg(sample_svg, credential_dict, overwrite=False)
        
        # Extract credential
        extracted = service.extract_svg(baked_svg)
        
        assert extracted is not None
        assert extracted["id"] == credential_dict["id"]
        assert extracted["type"] == credential_dict["type"]
    
    def test_extract_svg_not_found(self, sample_svg):
        """Test SVG extraction when no credential exists"""
        service = BadgeBakingService()
        
        extracted = service.extract_svg(sample_svg)
        
        assert extracted is None
    
    def test_bake_invalid_json(self, sample_png):
        """Test baking with invalid JSON credential"""
        service = BadgeBakingService()
        
        invalid_credential = {"invalid": "missing required fields"}
        
        # Should still bake (validation happens at API level)
        result = service.bake_png(sample_png, invalid_credential, overwrite=False)
        assert isinstance(result, bytes)

