# Login Page

**File:** `src/adamfit/pages/login.py`

## What you see
A username and password form. Until you log in, this is the only page in the app. The router in `app.py` hides every other page. See [authentication](authentication.md) for the bigger picture.

## How it works
1. A form collects the username and password. Because it is a form, typing does not rerun the page. Only clicking **Log in** does.
   ```python
   with st.form("login_form"):
       username = st.text_input("Username", autocomplete="username")
       password = st.text_input("Password", type="password", autocomplete="current-password")
       submitted = st.form_submit_button("Log in", type="primary")
   ```
2. On submit, the credentials are checked against the database. If the database can't be reached, the error is shown and the page stops.
   ```python
   try:
       user_id = auth.authenticate(username, password)
   except Exception as exc:
       st.error(f"Could not reach the database: {exc}")
       st.stop()
   ```
3. A wrong username or password shows the same message either way, so nobody can find out which usernames exist. On success, the user id is saved in the session and the app reruns. `app.py` now sees a logged-in user and shows the full menu.
   ```python
   if user_id is None:
       st.error("Incorrect username or password.")
   else:
       auth.log_in(user_id)
       st.rerun()
   ```

## Widgets used
- [st.title / st.subheader / st.caption](widgets/st_title.md): heading and the hint about creating an account
- [st.form / st.form_submit_button](widgets/st_form.md): groups the two fields
- [st.text_input](widgets/st_text_input.md): username, and password with `type="password"`
- [st.error](widgets/st_status_messages.md): wrong credentials or a database problem

## Core functions
- `authenticate` (`src/adamfit/auth.py`): checks the password against the stored Argon2 hash and records the login time. Returns the user id, or `None`.
  ```python
  user_id = auth.authenticate("adam", "my password")
  ```
- `log_in` (`src/adamfit/auth.py`): stores the user id in `st.session_state`, which is what "being logged in" means.
  ```python
  auth.log_in(user_id)
  ```

## Database tables used
- `app_user`: reads the password hash, and updates `last_login_at`.
