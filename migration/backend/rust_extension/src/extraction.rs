/*!
Badge extraction implementation for PNG and SVG
Extracts OpenBadgeCredential from baked badges
*/

use base64::{Engine as _, engine::general_purpose};
use png::Decoder;
use std::io::Cursor;
use crate::error::BakingError;

const OPENBADGE_KEYWORD: &str = "openbadgecredential";
const SVG_CREDENTIAL_TAG_START: &str = "<openbadges:credential";
const SVG_CREDENTIAL_TAG_END: &str = "</openbadges:credential>";

/// Extract credential from PNG image
/// Searches for iTXt chunk with keyword "openbadgecredential"
pub fn extract_png_impl(image_data_b64: &str) -> Result<Option<String>, BakingError> {
    // Decode base64 image data
    let image_data = general_purpose::STANDARD.decode(image_data_b64)?;
    
    // Decode PNG
    let decoder = Decoder::new(Cursor::new(&image_data));
    let reader = decoder.read_info()
        .map_err(|e| BakingError::PngDecodeError(e.to_string()))?;
    
    let info = reader.info().clone();
    
    // Search for openbadgecredential in iTXt chunks (UTF-8 text)
    for chunk in &info.utf8_text {
        if chunk.keyword == OPENBADGE_KEYWORD {
            return Ok(Some(chunk.text.clone()));
        }
    }
    
    // Also check compressed and uncompressed Latin-1 text chunks
    // (though iTXt should be preferred per spec)
    for chunk in &info.uncompressed_latin1_text {
        if chunk.keyword == OPENBADGE_KEYWORD {
            return Ok(Some(
                String::from_utf8_lossy(chunk.text.as_bytes()).to_string()
            ));
        }
    }
    
    for chunk in &info.compressed_latin1_text {
        if chunk.keyword == OPENBADGE_KEYWORD {
            return Ok(Some(
                String::from_utf8_lossy(chunk.text.as_bytes()).to_string()
            ));
        }
    }
    
    Ok(None)
}

/// Extract credential from SVG image
/// Searches for <openbadges:credential> tag
pub fn extract_svg_impl(svg_content: &str) -> Result<Option<String>, BakingError> {
    // Find credential tag
    if let Some(start) = svg_content.find(SVG_CREDENTIAL_TAG_START) {
        if let Some(verify_start) = svg_content[start..].find("verify=\"") {
            let verify_pos = start + verify_start + 8; // length of 'verify="'
            
            if let Some(quote_end) = svg_content[verify_pos..].find('"') {
                let credential_b64 = &svg_content[verify_pos..verify_pos + quote_end];
                
                // Decode base64
                let credential_bytes = general_purpose::STANDARD.decode(credential_b64)?;
                let credential_json = String::from_utf8(credential_bytes)?;
                
                return Ok(Some(credential_json));
            }
        }
    }
    
    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::baking::bake_svg_impl;
    
    #[test]
    fn test_extract_svg() {
        let svg = r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
</svg>"#;
        
        let credential = r#"{"id":"https://example.com/badge","type":["VerifiableCredential","OpenBadgeCredential"]}"#;
        
        // Bake credential
        let baked = bake_svg_impl(svg, credential, false).unwrap();
        
        // Extract credential
        let extracted = extract_svg_impl(&baked).unwrap();
        assert!(extracted.is_some());
        
        let extracted_json = extracted.unwrap();
        assert!(extracted_json.contains("https://example.com/badge"));
        assert!(extracted_json.contains("OpenBadgeCredential"));
    }
    
    #[test]
    fn test_extract_svg_not_found() {
        let svg = r#"<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="blue"/>
</svg>"#;
        
        let result = extract_svg_impl(svg).unwrap();
        assert!(result.is_none());
    }
}

