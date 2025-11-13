/*!
Badge Baking Rust Module
Implements Open Badge v3.0 badge baking and extraction for PNG and SVG images
*/

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

mod baking;
mod extraction;
mod error;

use error::BakingError;

/// Bake an OpenBadgeCredential into a PNG image
/// 
/// # Arguments
/// * `image_data` - Base64 encoded PNG image data
/// * `credential_json` - JSON string of the OpenBadgeCredential
/// * `overwrite` - Whether to overwrite existing credential data (default: false)
/// 
/// # Returns
/// Base64 encoded PNG image with baked credential
#[pyfunction]
#[pyo3(signature = (image_data, credential_json, overwrite=false))]
fn bake_png(
    image_data: String,
    credential_json: String,
    overwrite: bool
) -> PyResult<String> {
    baking::bake_png_impl(&image_data, &credential_json, overwrite)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Bake an OpenBadgeCredential into an SVG image
/// 
/// # Arguments
/// * `svg_content` - SVG image content as string
/// * `credential_json` - JSON string of the OpenBadgeCredential
/// * `overwrite` - Whether to overwrite existing credential data (default: false)
/// 
/// # Returns
/// SVG content with baked credential
#[pyfunction]
#[pyo3(signature = (svg_content, credential_json, overwrite=false))]
fn bake_svg(
    svg_content: String,
    credential_json: String,
    overwrite: bool
) -> PyResult<String> {
    baking::bake_svg_impl(&svg_content, &credential_json, overwrite)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Extract OpenBadgeCredential from a PNG image
/// 
/// # Arguments
/// * `image_data` - Base64 encoded PNG image data
/// 
/// # Returns
/// JSON string of the extracted OpenBadgeCredential, or None if not found
#[pyfunction]
fn extract_png(image_data: String) -> PyResult<Option<String>> {
    extraction::extract_png_impl(&image_data)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Extract OpenBadgeCredential from an SVG image
/// 
/// # Arguments
/// * `svg_content` - SVG image content as string
/// 
/// # Returns
/// JSON string of the extracted OpenBadgeCredential, or None if not found
#[pyfunction]
fn extract_svg(svg_content: String) -> PyResult<Option<String>> {
    extraction::extract_svg_impl(&svg_content)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Verify that a credential is valid JSON
#[pyfunction]
fn verify_credential_json(credential_json: String) -> PyResult<bool> {
    match serde_json::from_str::<serde_json::Value>(&credential_json) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false)
    }
}

/// Badge baking module for Python
#[pymodule]
fn badge_baking(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(bake_png, m)?)?;
    m.add_function(wrap_pyfunction!(bake_svg, m)?)?;
    m.add_function(wrap_pyfunction!(extract_png, m)?)?;
    m.add_function(wrap_pyfunction!(extract_svg, m)?)?;
    m.add_function(wrap_pyfunction!(verify_credential_json, m)?)?;
    Ok(())
}

