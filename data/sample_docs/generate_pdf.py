import os
import pymupdf

def create_sample_pdf(output_path: str):
    doc = pymupdf.open() # new empty document
    
    # Page 1: Overview & Password Policy
    page1 = doc.new_page()
    text1 = """ACCOUNT SECURITY AND AUTHENTICATION GUIDE
Version: v2.4 | Last Updated: 2024-02-15
Department: Enterprise IT Security & Identity Operations

1. Overview
This policy manual governs authentication and security credentials for all organizational personnel. All access to enterprise applications requires active multi-factor authentication and strict adherence to identity validation procedures.

2. Password Reset Procedures
To reset your account password, navigate to the Account Settings page on the employee portal and select "Reset Password". You will be prompted to enter your organizational email address and confirm your identity via an SMS or Authenticator App challenge.
Temporary password reset links remain valid for 15 minutes from issuance. If the link expires, a new reset request must be submitted through the portal.

3. Multi-Factor Authentication (MFA)
Multi-factor authentication is mandatory for all employee accounts. Employees may configure MFA using hardware security keys (FIDO2/WebAuthn), standard TOTP mobile authenticator applications (Google Authenticator, Microsoft Authenticator), or biometric device authentication. SMS-based MFA is restricted to secondary recovery fallback only."""
    
    page1.insert_text((50, 60), text1, fontsize=11, fontname="helv", lineheight=1.4)
    
    # Page 2: Lockout, Sessions & Single Sign-On
    page2 = doc.new_page()
    text2 = """ACCOUNT SECURITY AND AUTHENTICATION GUIDE (CONTINUED)
Version: v2.4 | Last Updated: 2024-02-15

4. Account Lockout and Inactivity Policies
To safeguard systems against brute-force attacks, an employee account is automatically locked after 5 consecutive failed login attempts. Once locked, the account remains inaccessible for a mandatory lockout period of 30 minutes.
For emergency unlock requests before the 30-minute lockout period elapses, the user must contact the IT Security Helpdesk and provide their verified employee identification number.

5. Session Timeout Thresholds
Active user sessions automatically time out after 15 minutes of user inactivity. Users will be required to re-authenticate with their credentials and active MFA token to resume access to protected internal tools.

6. Single Sign-On (SSO) Integration
Enterprise SSO is provisioned via Okta SAML 2.0. Users authenticating through corporate network gateways or approved VPN connections are automatically redirected to the central SSO gateway."""

    page2.insert_text((50, 60), text2, fontsize=11, fontname="helv", lineheight=1.4)
    
    doc.save(output_path)
    doc.close()
    print(f"Sample PDF created at: {output_path}")

if __name__ == "__main__":
    os.makedirs("./data/sample_docs", exist_ok=True)
    create_sample_pdf("./data/sample_docs/Account_Security_and_Authentication_Guide.pdf")
