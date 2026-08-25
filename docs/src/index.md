# HOPE Beneficiary Portal

## About

HOPE Beneficiary Portal lets beneficiaries securely access the information the system stores about their household and program participation.

After identity verification, the beneficiary can:

- View household profile and demographic details.
- View linked programs, payment statuses, and grievance tickets.
- Open a new issue (ticket) from the portal.
- Create or recover portal account credentials (username and password).

The portal includes anti-abuse protections: login attempts are rate-limited and repeated failed verification attempts can trigger temporary lockouts.

## Login methods (4 ways)

On the home page, users can enter through four supported methods:

### 1) Registration Number

- User provides the registration number received during enrollment.
- The system asks verification questions.
- After successful verification, the user is redirected to household/program/payment information.

### 2) SMS verification

- User provides the mobile number used during registration.
- The portal sends a one-time password (OTP) by SMS.
- After OTP verification, the user can access their household information and actions.

### 3) Email verification

- User provides the email used during registration.
- The portal sends a one-time password (OTP) by email.
- After OTP verification, the user can access their household information and actions.

### 4) Account login (username/password)

- User signs in with previously created beneficiary credentials.
- On success, the user is redirected directly to their household information view.
- From there, the user can review program/payment details and open an issue.

## Username and password

After identity verification (registration number, SMS, or email), the household page offers **Set username and password**.

- The beneficiary chooses a username and password (or a new password if an account already exists).
- Existing usernames can be retrieved on that screen; the previous password cannot be shown because it is stored hashed — a new password must be set instead.
- Credentials are shown once after save. On later visits, **Login** on the home page skips the registration-number flow.
