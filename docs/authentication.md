# Authentication

How logging in works in AdamFit, why it was built this way, and what to add later.

## The pieces
| Piece | Where | What it does |
|-------|-------|--------------|
| `app_user.password_hash` | database | Stores an **Argon2 hash**, never the password itself |
| `adamfit-create-user` | `src/adamfit/cli/create_user.py` | The only way to create a user (there is no sign-up page) |
| `authenticate()` | `src/adamfit/auth.py` | Checks a username and password against the hash |
| `st.session_state["user_id"]` | Streamlit | Being "logged in" means this key is set for your browser tab |
| Router | `src/adamfit/app.py` | Shows only the login page until `user_id` is set |

## Creating a user
```bash
uv run adamfit-create-user adam
```
It prompts for the password twice (8+ characters). Usernames are stored in lowercase, and login is case-insensitive. A database trigger gives every new user their own copy of the starter food list (`standard_food`).

## Why these choices
- **Hashing with Argon2** (via `argon2-cffi`). A hash is one-way: the app can check a password but nobody, including you with database access, can read it back. Argon2 is deliberately slow, which makes guessing expensive. Each hash includes a random salt, so two identical passwords produce different hashes.
- **No sign-up page.** While it's just you, open registration would let anyone on your network create an account. A terminal command is simpler and safer.
- **Same error for a wrong username or a wrong password.** `authenticate()` even hashes a dummy value when the username doesn't exist, so both cases take the same time and nobody can find out which usernames exist.
- **Router-level protection.** Pages aren't individually guarded. `app.py` simply doesn't register them for logged-out visitors, so there's nothing to reach by URL.
- **Google Health never logs you in.** When Google sends you back after connecting Google Health, that tab is a new, logged-out session. `app.py` only stores the Google tokens for the user who started the connection (found by a one-time value in the database) and shows a message on the login page. See [Google Health setup](google_health_setup.md#how-syncing-works).
- **Not Streamlit's built-in `st.login`.** It uses an external identity provider (Google, Auth0, ...) over OpenID Connect. That's the right move for a public, multi-user deployment, but overkill for a local app.

## Known limitations (fine for local use)
- **Refreshing the browser logs you out.** `st.session_state` lives only as long as the browser tab's connection. Fix later with a signed "remember me" cookie, or with `st.login`.
- **No lockout after repeated wrong passwords.** Add a failed-attempt counter before exposing the app beyond localhost.
- **No password change page.** Add one later (`users.update_password_hash` already exists).
- Run behind HTTPS if the app is ever reachable from another machine.
