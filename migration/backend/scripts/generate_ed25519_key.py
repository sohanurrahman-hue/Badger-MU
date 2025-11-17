# keygen_and_utils.py
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64, json, hashlib
from pathlib import Path

def b64url_no_pad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")

def int_to_b64url(n: int) -> str:
    # Big-endian, minimal-length byte array
    length = (n.bit_length() + 7) // 8
    return b64url_no_pad(n.to_bytes(length, "big"))

def generate_rsa_keypair(bits: int = 2048):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits, backend=default_backend())
    public_key = private_key.public_key()
    # PEM (you’ll use these to actually sign/verify)
    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ).decode("utf-8")
    pub_pem = public_key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    public_path = Path(__file__).parent.parent / "public_key.pem"
    with open(public_path, "wb") as f:
        f.write(pub_pem.encode("utf-8"))
    private_path = Path(__file__).parent.parent / "private_key.pem"
    with open(private_path, "wb") as f:
        f.write(priv_pem.encode("utf-8"))

    return private_path, public_path

def header_for_jwt():
    """Generate a header for a JWT"""

    with open("private_key.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    public_key = private_key.public_key()
    numbers = public_key.public_numbers()
    e = numbers.e
    n = numbers.n

    jwk_pub = {
        "kty": "RSA",
        "n": int_to_b64url(n),
        "e": int_to_b64url(e),
    }

    return jwk_pub

if __name__ == "__main__":
    private_path, public_path = generate_rsa_keypair()
    print("PRIVATE PATH:\n", private_path)
    print("PUBLIC PATH:\n", public_path)

# """
# Generate Ed25519 key pair for badge signing

# This script generates a private key file (private_key.pem) that is required
# for signing badges with EdDSA (Ed25519) algorithm.

# Usage:
#     python scripts/generate_ed25519_key.py
# """
# import sys
# from pathlib import Path

# # Add parent directory to path
# backend_dir = Path(__file__).parent.parent
# if str(backend_dir) not in sys.path:
#     sys.path.insert(0, str(backend_dir))

# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric import ed25519
# import os

# def generate_key_pair():
#     """Generate Ed25519 key pair and save private key to file"""
    
#     print("Generating Ed25519 key pair...")
    
#     # Generate private key
#     private_key = ed25519.Ed25519PrivateKey.generate()
    
#     # Serialize private key to PEM format
#     private_pem = private_key.private_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PrivateFormat.PKCS8,
#         encryption_algorithm=serialization.NoEncryption()
#     )
    
#     # Get public key
#     public_key = private_key.public_key()
    
#     # Serialize public key to PEM format
#     public_pem = public_key.public_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PublicFormat.SubjectPublicKeyInfo
#     )
    
#     # Save private key to file (in backend directory)
#     private_key_path = backend_dir / "private_key.pem"
#     with open(private_key_path, "wb") as f:
#         f.write(private_pem)
    
#     print(f"✓ Private key saved to: {private_key_path}")
    
#     # Save public key to file (optional, for reference)
#     public_key_path = backend_dir / "public_key.pem"
#     with open(public_key_path, "wb") as f:
#         f.write(public_pem)
    
#     print(f"✓ Public key saved to: {public_key_path}")
    
#     # Display public key info
#     raw_public_bytes = public_key.public_bytes(
#         encoding=serialization.Encoding.Raw,
#         format=serialization.PublicFormat.Raw
#     )
    
#     import base64
#     x_b64u = base64.urlsafe_b64encode(raw_public_bytes).rstrip(b'=').decode('utf-8')
    
#     print("\nPublic Key JWK:")
#     print(f"  kty: OKP")
#     print(f"  crv: Ed25519")
#     print(f"  x: {x_b64u}")
    
#     print("\n✓ Key pair generated successfully!")
#     print("\n⚠️  IMPORTANT: Keep private_key.pem secure and never commit it to version control!")
    
#     return private_key_path, public_key_path


# if __name__ == "__main__":
#     # Check if key already exists
#     private_key_path = backend_dir / "private_key.pem"
#     if private_key_path.exists():
#         response = input(f"private_key.pem already exists. Overwrite? (y/N): ")
#         if response.lower() != 'y':
#             print("Aborted.")
#             sys.exit(0)
    
#     try:
#         generate_key_pair()
#     except Exception as e:
#         print(f"✗ Error generating key pair: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)

