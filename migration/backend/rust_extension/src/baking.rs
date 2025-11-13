/*!
Badge baking implementation for PNG and SVG
Follows Open Badge v3.0 specification:
- PNG: iTXt chunk with keyword "openbadgecredential"
- SVG: <openbadges:credential> tag
*/

use base64::{Engine as _, engine::general_purpose};
use png::{Decoder, Encoder, ColorType, BitDepth, Compression};
use std::io::Cursor;
use crate::error::BakingError;

const OPENBADGE_KEYWORD: &str = "openbadgecredential";
const SVG_CREDENTIAL_TAG_START: &str = "<openbadges:credential";
const SVG_CREDENTIAL_TAG_END: &str = "</openbadges:credential>";

/// Bake credential into PNG image
/// Adds iTXt chunk with keyword "openbadgecredential" per Open Badge v3.0 spec
pub fn bake_png_impl(
    image_data_b64: &str,
    credential_json: &str,
    overwrite: bool
) -> Result<String, BakingError> {
    // Validate credential JSON
    serde_json::from_str::<serde_json::Value>(credential_json)?;
    
    // Decode base64 image data
    let image_data = general_purpose::STANDARD.decode(image_data_b64)?;
    
    // Decode PNG
    let decoder = Decoder::new(Cursor::new(&image_data));
    let reader = decoder.read_info()
        .map_err(|e| BakingError::PngDecodeError(e.to_string()))?;
    
    let mut reader = reader;
    let info = reader.info().clone();
    
    // Check if credential already exists
    if !overwrite {
        for chunk in &info.compressed_latin1_text {
            if chunk.keyword == OPENBADGE_KEYWORD {
                return Err(BakingError::CredentialExists);
            }
        }
        for chunk in &info.uncompressed_latin1_text {
            if chunk.keyword == OPENBADGE_KEYWORD {
                return Err(BakingError::CredentialExists);
            }
        }
        for chunk in &info.utf8_text {
            if chunk.keyword == OPENBADGE_KEYWORD {
                return Err(BakingError::CredentialExists);
            }
        }
    }
    
    // Read image data
    let mut buf = vec![0; reader.output_buffer_size()];
    let frame_info = reader.next_frame(&mut buf)
        .map_err(|e| BakingError::PngDecodeError(e.to_string()))?;
    let bytes = &buf[..frame_info.buffer_size()];
    
    // Create new PNG with credential
    let mut output = Vec::new();
    {
        let mut encoder = Encoder::new(
            &mut output,
            info.width,
            info.height
        );
        
        encoder.set_color(info.color_type);
        encoder.set_depth(info.bit_depth);
        encoder.set_compression(Compression::Default);
        
        // Add iTXt chunk with credential
        encoder.add_itxt_chunk(
            OPENBADGE_KEYWORD.to_string(),
            credential_json.to_string()
        ).map_err(|e| BakingError::PngEncodeError(e.to_string()))?;
        
        let mut writer = encoder.write_header()
            .map_err(|e| BakingError::PngEncodeError(e.to_string()))?;
        
        writer.write_image_data(bytes)
            .map_err(|e| BakingError::PngEncodeError(e.to_string()))?;
    }
    
    // Encode to base64
    Ok(general_purpose::STANDARD.encode(&output))
}

/// Bake credential into SVG image
/// Adds <openbadges:credential> tag per Open Badge v3.0 spec
pub fn bake_svg_impl(
    svg_content: &str,
    credential_json: &str,
    overwrite: bool
) -> Result<String, BakingError> {
    // Validate credential JSON
    serde_json::from_str::<serde_json::Value>(credential_json)?;
    
    // Check if credential already exists
    if !overwrite && svg_content.contains(SVG_CREDENTIAL_TAG_START) {
        return Err(BakingError::CredentialExists);
    }
    
    // Remove existing credential if overwriting
    let mut svg = svg_content.to_string();
    if overwrite {
        if let Some(start) = svg.find(SVG_CREDENTIAL_TAG_START) {
            if let Some(end) = svg[start..].find(SVG_CREDENTIAL_TAG_END) {
                let end_pos = start + end + SVG_CREDENTIAL_TAG_END.len();
                svg.drain(start..end_pos);
            }
        }
    }
    
    // Base64 encode the credential for embedding
    let credential_b64 = general_purpose::STANDARD.encode(credential_json.as_bytes());
    
    // Create openbadges:credential tag
    let credential_tag = format!(
        r#"<openbadges:credential xmlns:openbadges="https://purl.imsglobal.org/ob/v3p0" verify="{}"/>"#,
        credential_b64
    );
    
    // Find closing </svg> tag and insert credential before it
    if let Some(svg_close_pos) = svg.rfind("</svg>") {
        svg.insert_str(svg_close_pos, &credential_tag);
        svg.insert(svg_close_pos, '\n');
        Ok(svg)
    } else {
        Err(BakingError::SvgError("Could not find closing </svg> tag".to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_bake_svg() {
        let svg = r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
</svg>"#;
        
        let credential = r#"{"id":"https://example.com/badge","type":["VerifiableCredential","OpenBadgeCredential"]}"#;
        
        let result = bake_svg_impl(svg, credential, false);
        assert!(result.is_ok());
        
        let baked = result.unwrap();
        assert!(baked.contains("<openbadges:credential"));
        assert!(baked.contains("xmlns:openbadges"));
    }
    
    #[test]
    fn test_bake_svg_already_exists() {
        let svg = r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
<openbadges:credential xmlns:openbadges="https://purl.imsglobal.org/ob/v3p0" verify="test"/>
</svg>"#;
        
        let credential = r#"{"id":"https://example.com/badge"}"#;
        
        let result = bake_svg_impl(svg, credential, false);
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), BakingError::CredentialExists));
    }
    
    #[test]
    fn test_bake_svg_overwrite() {
        let svg = r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
<openbadges:credential xmlns:openbadges="https://purl.imsglobal.org/ob/v3p0" verify="old"/>
</svg>"#;
        
        let credential = r#"{"id":"https://example.com/badge","new":true}"#;
        
        let result = bake_svg_impl(svg, credential, true);
        assert!(result.is_ok());
        
        let baked = result.unwrap();
        assert!(baked.contains("\"new\":true"));
        assert!(!baked.contains("verify=\"old\""));
    }
}

