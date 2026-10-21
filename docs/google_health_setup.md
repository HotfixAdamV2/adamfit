# Google Health (Fitbit) setup

How AdamFit gets permission to read data from Google Health, where your Fitbit
syncs to. Read this if you set up a new machine, the credentials stop working,
or you want to sync a new kind of data.

## The big picture

- **Google Health API.** This is Google's replacement for the old Fitbit Web
  API, which was switched off on October 30, 2026. AdamFit talks to
  `https://health.googleapis.com/v4/...`.
- **OAuth 2.0.** This is how AdamFit gets permission. AdamFit sends you to a
  Google page, you approve, and Google sends you back with a one-time code. The
  app swaps that code for:
  - an **access token**, which works for about an hour and is sent with each
    API call;
  - a **refresh token**, which is used to get new access tokens without asking
    you again.
- **Google Cloud project.** This is AdamFit's registration with Google. It
  gives the app a **client ID** (its public name) and a **client secret** (its
  password).

## One-time setup in Google Cloud Console

Google sometimes renames these menus. If a label doesn't match, look for the
nearest equivalent.

0. **Phone.** In the Google Health app, check you're signed in with the same
   Google account you'll use below. Your Fitbit data must be linked to that
   account, or the login fails.
1. **Create a project.** Go to [console.cloud.google.com](https://console.cloud.google.com),
   open the project picker, choose **New Project**, and name it `adamfit`. You
   don't need billing.
2. **Enable the API.** Search for **Google Health API** and click **Enable**.
3. **Consent screen.** This is the page Google shows when the app asks for
   permission. Find it under **APIs & Services → OAuth consent screen**, also
   called **Google Auth Platform**.
   - App name: `AdamFit`
   - Support email: your Gmail address
   - Audience: **External** ("Internal" only works for Workspace
     organisations)
4. **Test users.** Under **Audience**, the publishing status should be
   **Testing**. Add your Gmail address as a test user. Only people on this list
   can log in.
5. **Scopes.** A scope is a permission the app can ask for. Under **Data
   Access → Add or remove scopes**, these four are enabled, all read-only:
   - `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly`
   - `https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly`
     (weight is in this one)
   - `https://www.googleapis.com/auth/googlehealth.nutrition.readonly`
   - `https://www.googleapis.com/auth/googlehealth.sleep.readonly`
6. **Client.** Under **Clients** (or **Credentials**), choose **Create client**.
   - Application type: **Web application**
   - Name: `adamfit-local`
   - Authorized redirect URI: `http://localhost:8501/`, with the trailing
     slash. After you approve, Google sends you back to this address, which is
     where Streamlit runs.
   - Copy the **Client ID** and **Client secret** shown at the end.

## Credentials in `.env`

Put these in the **root** `.env`, next to `pyproject.toml`. It is git-ignored,
so never commit it, and never paste the secret anywhere.

```
GOOGLE_HEALTH_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_HEALTH_CLIENT_SECRET=GOCSPX-...
GOOGLE_HEALTH_REDIRECT_URI=http://localhost:8501/
```

`.env.example` has the same names with blank values.

If the secret leaks, go to **Clients → adamfit-local**, add a new secret,
update `.env`, then delete the old secret.

## Connecting for the first time

1. In AdamFit, go to **My Profile → Weight**, open **Google Health sync**
   and click **Connect Google Health**. Google opens in a new tab.
2. Google warns **"Google hasn't verified this app"**. This is expected for
   your own test app. Click **Continue**.
3. Approve the permissions. Leave every box ticked; weight needs the
   "health metrics and measurements" one.
4. Google sends that new tab back to AdamFit, which shows the AdamFit login
   page with a green "Google Health connected" message (or a red message
   saying what went wrong). Close that tab.
5. In your original AdamFit tab, click **Refresh status**. The date pickers
   and **Sync now** appear.

## Things to remember

- **Weekly reconnect.** While the app is in **Testing** mode, Google's
  refresh tokens expire after **7 days**, so you will have to reconnect about
  once a week. Switching the project to **In Production** (under **Audience**)
  should stop that. Below 100 users there should be no review needed, but this
  hasn't been tested yet.
- **100-user cap.** An unverified app is limited to 100 users. Going past that
  needs Google's security review, which isn't relevant for a personal app.
- **No sandbox.** The API has no test environment, so everything runs against
  your real data. AdamFit only asks for read-only scopes.
- **New data types.** Nutrition, sleep and activity scopes are already
  enabled, so syncing those later won't need any Cloud Console changes. After
  the code changes, reconnect once so the app asks for the new permissions.

## How syncing works

### Connecting, and why a new tab
Login in AdamFit lives in `st.session_state`, which belongs to one browser
tab. When Google sends you back to `http://localhost:8501/?code=...&state=...`,
that arrives in a **new session that isn't logged in**. So:

1. When the Connect button is drawn, AdamFit makes a random one-time
   **state** value, saves it in your `google_health_connection` row (valid for
   10 minutes) and puts it in the Google link. The button opens the link in a
   new tab, so your original tab stays logged in.
2. When Google redirects back, `app.py` runs **before** any login check. It
   looks up which user that state belongs to, clears it so it can't be used
   twice, swaps the one-time `code` for tokens, and checks the account with
   Google Health (`/v4/users/me/identity`). Only then are the tokens saved.
3. It **never logs anyone in**. It clears the code from the address bar and
   shows the result on the login page. You go back to your original tab and
   click **Refresh status**.

If the link is more than 10 minutes old, or was already used, you get a
message asking you to try again. If your Google account isn't linked to
Google Health, you are told to check the Google Health app on your phone.

### What a sync does
1. Gets a working access token. Access tokens last about an hour; one that
   expires within 60 seconds is swapped for a new one using the refresh token.
2. Downloads every weight data point between the two dates you picked
   (both included), page by page.
3. Works out the **local day** of each weigh-in (the date where you were, not
   UTC), and keeps only the **latest weigh-in of each day**.
4. Saves one row per day in `user_weight` with `source = 'google_health'`.
   This **overwrites** whatever was stored for that day, including a weight
   you typed in by hand. Days with no Fitbit weigh-in are left alone.
5. Records `last_synced_at`. Next time, the start date defaults to that day.

The weight table shows each entry's source as **Fitbit** or **Manual**.
Typing a weight for a day that was synced turns it back into **Manual**,
until a later sync of that day overwrites it again.

### Weekly reconnect
While the Google Cloud app is in **Testing** mode, the refresh token stops
working after 7 days. The next sync then shows "Your Google Health connection
has expired", AdamFit forgets the old tokens, and the Connect button comes
back. Connect again and carry on.

**Disconnect** asks Google to cancel AdamFit's access (if Google can't be
reached, that step is skipped) and then forgets the tokens.

### Where the code lives
| File | What it does |
|------|--------------|
| `src/adamfit/google_health.py` | Settings, login link, callback, token refresh, downloading and picking weigh-ins, `sync_weights` |
| `src/adamfit/google_health_connection.py` | SQL for the `google_health_connection` table (state, tokens, last synced) |
| `src/adamfit/weights.py` | `save_synced_weights` (overwrite per day) and `save_weight` (manual) |
| `src/adamfit/app.py` | Finishes the connection when Google redirects back |
| `src/adamfit/pages/profile.py` | The **Google Health sync** section of the Weight tab ([page doc](profile_page.md)) |

Tokens and the client secret are never printed, logged or shown in error
messages.

## Useful links

- [About the Google Health API](https://developers.google.com/health/about)
- [Set up Google Cloud and OAuth](https://developers.google.com/health/setup)
- [REST reference](https://developers.google.com/health/reference/rest)
- [Listing data points](https://developers.google.com/health/reference/rest/v4/users.dataTypes.dataPoints/list)
