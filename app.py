import streamlit as st
import streamlit_authenticator as stauth
from st_pages import add_page_title, get_nav_from_toml

usernames = ["Tracy", "NamHai"]
names     = ["Tracy", "Nam Hai"]
passwords = ["123", "456"]

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[i]: {
            "name": names[i],
            "password": hashed_passwords[i]
        }
        for i in range(len(usernames))
    }
}

cookie_name   = "my_streamlit_app"
cookie_key    = "some_random_secret_key"      
cookie_expiry = 1  

authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    cookie_expiry
)

name, authentication_status, username = authenticator.login("Sign In", "main")

if authentication_status:
    st.sidebar.write(f"👤 Welcome, **{name}**")
    authenticator.logout("Sign Out", "sidebar")

    nav = get_nav_from_toml(".streamlit/pages.toml")
    pg = st.navigation(nav)
    add_page_title(pg)
    pg.run()

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")
elif authentication_status is None:
    st.warning("⚠️ Please enter your username and password")

