# Home Page

**File:** `src/adamfit/pages/home.py`

## What you see
A greeting with your username and a link to the My Profile page. You only see this page after logging in.

## How it works
1. The logged-in user is loaded from the database.
   ```python
   user = auth.current_user()
   ```
2. The heading greets them by name, followed by the welcome text.
   ```python
   st.title(f"Welcome, {user['username']}")
   st.write("Welcome to my personal fitness app.")
   ```
3. A link takes them to the profile page.
   ```python
   st.page_link("pages/profile.py", label="Log your weight on My Profile", icon=":material/monitor_weight:")
   ```

## Widgets used
- [st.title](widgets/st_title.md): the greeting
- [st.write](widgets/st_write.md): the welcome text
- [st.page_link](widgets/st_navigation.md): link to My Profile

## Core functions
- `current_user` (`src/adamfit/auth.py`): looks up who is logged in (from `st.session_state`) and loads their profile from the database.
  ```python
  user = auth.current_user()
  ```

## Database tables used
- `app_user`: read only.
