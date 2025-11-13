"""
Badge Service - Badge baking and extraction
Wraps Rust badge_baking module with fallback to Python implementation
"""
import base64
import json
import logging
from typing import Optional
from io import BytesIO
from PIL import Image, PngImagePlugin

logger = logging.getLogger(__name__)

# Try to import Rust extension
try:
    import badge_baking
    RUST_AVAILABLE = True
    logger.info("Rust badge_baking module loaded successfully")
except ImportError:
    RUST_AVAILABLE = False
    logger.warning("Rust badge_baking module not available, using Python fallback")


class BadgeBakingService:
    """
    Service for baking OpenBadgeCredentials into images
    Uses Rust implementation when available, falls back to Python
    """
    
    @staticmethod
    def bake_png(image_data: bytes, credential: dict, overwrite: bool = False) -> bytes:
        """
        Bake credential into PNG image
        
        Args:
            image_data: PNG image bytes
            credential: OpenBadgeCredential as dict
            overwrite: Whether to overwrite existing credential
            
        Returns:
            PNG image bytes with baked credential
        """
        credential_json = json.dumps(credential, separators=(',', ':'))
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        if RUST_AVAILABLE:
            try:
                result_b64 = badge_baking.bake_png(image_b64, credential_json, overwrite)
                return base64.b64decode(result_b64)
            except Exception as e:
                logger.error(f"Rust bake_png failed: {e}, falling back to Python")
        
        # Python fallback
        return BadgeBakingService._bake_png(image_data, credential_json, overwrite)
    
    @staticmethod
    def bake_svg(svg_content: str, credential: dict, overwrite: bool = False) -> str:
        """
        Bake credential into SVG image
        
        Args:
            svg_content: SVG content as string
            credential: OpenBadgeCredential as dict
            overwrite: Whether to overwrite existing credential
            
        Returns:
            SVG content with baked credential
        """
        credential_json = json.dumps(credential, separators=(',', ':'))
        
        if RUST_AVAILABLE:
            try:
                return badge_baking.bake_svg(svg_content, credential_json, overwrite)
            except Exception as e:
                logger.error(f"Rust bake_svg failed: {e}, falling back to Python")
        
        # Python fallback
        return BadgeBakingService._bake_svg(svg_content, credential_json, overwrite)
    
    @staticmethod
    def extract_png(image_data: bytes) -> Optional[dict]:
        """
        Extract credential from PNG image
        
        Args:
            image_data: PNG image bytes
            
        Returns:
            OpenBadgeCredential as dict, or None if not found
        """
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        if RUST_AVAILABLE:
            try:
                result = badge_baking.extract_png(image_b64)
                if result:
                    return json.loads(result)
                return None
            except Exception as e:
                logger.error(f"Rust extract_png failed: {e}, falling back to Python")
        
        # Python fallback
        credential_json = BadgeBakingService._extract_png_python(image_data)
        if credential_json:
            return json.loads(credential_json)
        return None
    
    @staticmethod
    def extract_svg(svg_content: str) -> Optional[dict]:
        """
        Extract credential from SVG image
        
        Args:
            svg_content: SVG content as string
            
        Returns:
            OpenBadgeCredential as dict, or None if not found
        """
        if RUST_AVAILABLE:
            try:
                result = badge_baking.extract_svg(svg_content)
                if result:
                    return json.loads(result)
                return None
            except Exception as e:
                logger.error(f"Rust extract_svg failed: {e}, falling back to Python")
        
        # Python fallback
        credential_json = BadgeBakingService._extract_svg_python(svg_content)
        if credential_json:
            return json.loads(credential_json)
        return None
    
    # ========================================================================
    # Python Fallback Implementations
    # ========================================================================
    
    @staticmethod
    def _bake_png(image_data: bytes, credential_json: str, overwrite: bool) -> bytes:
        """Python fallback for PNG baking"""
        # Load image
        img = Image.open(BytesIO(image_data))
        
        # Check for existing credential
        if not overwrite and "openbadgecredential" in img.info:
            raise ValueError("Credential already exists in image. Use overwrite=true to replace.")
        
        # Create metadata
        metadata = PngImagePlugin.PngInfo()
        
        # Copy existing metadata except openbadgecredential
        for key, value in img.info.items():
            if key != "openbadgecredential":
                metadata.add_itxt(key, value)
        
        # Add credential
        metadata.add_itxt("openbadgecredential", credential_json)
        
        # Save with metadata
        output = BytesIO()
        img.save(output, format="PNG", pnginfo=metadata)
        return output.getvalue()
    
    @staticmethod
    def _bake_svg(svg_content: str, credential_json: str, overwrite: bool) -> str:
        """Python fallback for SVG baking"""
        # Check for existing credential
        if not overwrite and "<openbadges:credential" in svg_content:
            raise ValueError("Credential already exists in SVG. Use overwrite=true to replace.")
        
        # Remove existing credential if overwriting
        svg = svg_content
        if overwrite:
            start = svg.find("<openbadges:credential")
            if start != -1:
                end = svg.find("</openbadges:credential>", start)
                if end != -1:
                    svg = svg[:start] + svg[end + len("</openbadges:credential>"):]
        
        # Encode credential
        credential_b64 = base64.b64encode(credential_json.encode('utf-8')).decode('utf-8')
        
        # Create credential tag
        credential_tag = f'\n<openbadges:credential xmlns:openbadges="https://purl.imsglobal.org/ob/v3p0" verify="{credential_b64}"/>\n'
        
        # Insert before closing </svg>
        svg_close = svg.rfind("</svg>")
        if svg_close == -1:
            raise ValueError("Could not find closing </svg> tag")
        
        return svg[:svg_close] + credential_tag + svg[svg_close:]
    
    @staticmethod
    def _extract_png(image_data: bytes) -> Optional[str]:
        """Python fallback for PNG extraction"""
        img = Image.open(BytesIO(image_data))
        return img.info.get("openbadgecredential")
    
    @staticmethod
    def _extract_svg(svg_content: str) -> Optional[str]:
        """Python fallback for SVG extraction"""
        start = svg_content.find("<openbadges:credential")
        if start == -1:
            return None
        
        verify_start = svg_content.find('verify="', start)
        if verify_start == -1:
            return None
        
        verify_start += len('verify="')
        verify_end = svg_content.find('"', verify_start)
        if verify_end == -1:
            return None
        
        credential_b64 = svg_content[verify_start:verify_end]
        credential_bytes = base64.b64decode(credential_b64)
        return credential_bytes.decode('utf-8')


# Singleton instance
badge_service = BadgeBakingService()

