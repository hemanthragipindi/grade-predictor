# Nexora | Authentication & Security Documentation

## 1. User Flow Overview
The system follows a professional, linear authentication lifecycle:
1. **Registration**: User provides name, email, and mobile. The system validates uniqueness.
2. **Authentication**: User logs in via a two-step mobile verification process.
3. **Session Management**: Upon success, a secure session cookie is stored in the browser.
4. **Authorized Access**: The user is redirected to the Dashboard. All internal routes are now unlocked.
5. **Termination**: Logging out destroys the session and clears all browser-side credentials.

## 2. Technical Architecture
### Password Security
- **Hashing**: We utilize the `Werkzeug` security library. We never store plain-text passwords. Instead, we store a **Salted SHA-256 Hash**.
- **Validation**: During login, the system hashes the entered password and compares it to the stored hash.

### Session Persistence
- **Flask-Login**: This extension manages the "Current User" state across the entire application.
- **Timeout**: For security, sessions are configured with a **20-minute expiration** (`PERMANENT_SESSION_LIFETIME`).

## 3. Data Isolation (Multi-User Support)
The system is built on a "Tenant-Isolation" model:
- **Foreign Keys**: Every entry in the `subjects` and `cloud_files` tables is linked to a specific `user_id`.
- **Query Restriction**: The backend logic (e.g., `CloudFile.query.filter_by(user_id=current_user.id)`) ensures that users can only interact with their own data.

## 4. Testing & QA Checklist
| Test Case | Action | Expected Outcome |
| :--- | :--- | :--- |
| **New Signup** | Register with unique mobile | Redirect to Login with success toast. |
| **Duplicate Mobile** | Try to register with same mobile | Error: "Mobile number already registered." |
| **Incorrect Login** | Enter wrong password | Error: "Invalid mobile or password." |
| **Route Protection** | Try accessing `/dashboard` while logged out | Redirected to Login page. |
| **Admin Access** | Log in with master credentials | Direct access to Admin Command Center. |

## 5. Viva / Presentation Script
> "Our application implements a robust, session-based authentication system. We prioritize security by using industry-standard salted hashing for passwords, ensuring that even in a database leak, user credentials remain secure. Furthermore, we've implemented strict data isolation, where every academic artifact and prediction is cryptographically linked to the authenticated user's ID, preventing unauthorized data cross-talk."
