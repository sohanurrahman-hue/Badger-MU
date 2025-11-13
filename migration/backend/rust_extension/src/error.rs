/*!
Error types for badge baking
*/

use thiserror::Error;

#[derive(Error, Debug)]
pub enum BakingError {
    #[error("Invalid base64 encoding: {0}")]
    Base64Error(#[from] base64::DecodeError),
    
    #[error("PNG decoding error: {0}")]
    PngDecodeError(String),
    
    #[error("PNG encoding error: {0}")]
    PngEncodeError(String),
    
    #[error("Credential already exists in image. Use overwrite=true to replace.")]
    CredentialExists,
    
    #[error("Invalid credential JSON: {0}")]
    InvalidJson(#[from] serde_json::Error),
    
    #[error("SVG parsing error: {0}")]
    SvgError(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Invalid UTF-8: {0}")]
    Utf8Error(#[from] std::string::FromUtf8Error),
}

