import os
import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
import plotly.express as px
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import requests

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Mall Customer Dashboard", layout="wide")

# ---------------- HELPERS ----------------
def load_lottieurl(url: str, timeout: int = 6):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

# small animations (login + tiny header accent)
LOTTIE_LOGIN = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json")
LOTTIE_SPARK = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_touohxv0.json")

# ---------------- DATA PATHS (as in your original app) ----------------
USERS_CSV = "user.csv"
MALLS_CSV = "mall_brances.csv"
DATA_CSV = "Mall_Customers.csv"
  # kept same name as original read attempt

# ---------------- DATA LOADERS ----------------
@st.cache_data
def load_users():
    try:
        return pd.read_csv(USERS_CSV)
    except Exception:
        # return empty DF with expected columns so the rest of app keeps working
        return pd.DataFrame(columns=["username", "password", "role"])

@st.cache_data
def load_data():
    try:
        return pd.read_csv(DATA_CSV)
    except Exception:
        return pd.DataFrame()

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.username = ""

users = load_users()

# ---------------- STYLES ----------------
LOGIN_CSS = """
<style>
/* hide menu/footer when showing login card */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.login-card {
    background-color: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
    padding: 24px;
    border-radius: 14px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.12);
    max-width: 420px;
    margin-left: auto;
    margin-right: auto;
}

/* constrain internal inputs */
.login-card .stTextInput, .login-card .stNumberInput {
    max-width: 360px;
    margin-left: auto;
    margin-right: auto;
}

/* gradient button inside card */
.login-card .stButton > button {
    background: linear-gradient(90deg,#ff914d,#ff4d6d);
    color: white;
    border-radius: 20px;
    padding: 10px 20px;
    border: none;
    font-weight: 600;
}
.login-card .stButton > button:hover {
    transform: translateY(-2px);
}
</style>
"""

# ---------------- LOGIN PAGE ----------------
def login_page():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        # show lottie animation for login
        if LOTTIE_LOGIN is not None:
            try:
                st_lottie(LOTTIE_LOGIN, height=170, key="login_lottie")
            except Exception:
                pass

        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; margin-bottom:6px;'>Mall Dashboard Login</h3>", unsafe_allow_html=True)

        users_df = load_users()
        if users_df.empty:
            st.info("User file not found or empty. You can create an initial admin user by entering credentials below.")

        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", placeholder="Enter username")
            password_input = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Login")

            if submitted:
                # If users file empty -> create initial admin user and save
                if users_df.empty:
                    if username_input.strip() and password_input.strip():
                        new_df = pd.DataFrame([[username_input.strip(), password_input.strip(), "admin"]],
                                              columns=["username", "password", "role"])
                        # attempt saving
                        try:
                            os.makedirs(os.path.dirname(USERS_CSV), exist_ok=True)
                            new_df.to_csv(USERS_CSV, index=False)
                            st.success(f"Initial admin user created at {USERS_CSV}. Please login again.")
                        except Exception as e:
                            st.error(f"Failed to save user file: {e}")
                    else:
                        st.error("Provide username and password to create initial admin user.")
                else:
                    # validate against users csv (case-insensitive username)
                    matched = users_df[
                        (users_df['username'].astype(str).str.strip().str.lower() == str(username_input).strip().lower()) &
                        (users_df['password'].astype(str).str.strip() == str(password_input).strip())
                    ]
                    if not matched.empty:
                        role_value = str(matched.iloc[0]['role']).strip().lower()
                        st.session_state.logged_in = True
                        st.session_state.user_role = role_value
                        st.session_state.username = str(matched.iloc[0]['username']).strip()
                        # explicit rerun to load post-login UI
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- ADMIN DASHBOARD ----------------
def admin_dashboard():
    # small accent animation in header if available
    if LOTTIE_SPARK is not None:
        try:
            st_lottie(LOTTIE_SPARK, height=70, key="admin_spark")
        except Exception:
            pass

    st.header("Admin Dashboard")
    menu = st.selectbox("Choose Action", ["Manage Users", "Manage Malls"])

    def safe_save_csv(df, path):
        """
        Attempts to save df to the given path. If permission denied,
        falls back to current working directory.
        """
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            df.to_csv(path, index=False)
        except PermissionError:
            fallback_path = os.path.join(os.getcwd(), os.path.basename(path))
            df.to_csv(fallback_path, index=False)
            st.warning(f"Permission denied at {path}. Saved file instead to {fallback_path}")
        except Exception as e:
            st.error(f"Failed to save file at {path}: {e}")

    if menu == "Manage Users":
        users_df = load_users()
        st.subheader("User List")
        st.dataframe(users_df)

        st.subheader("Add New User")
        with st.form("add_user"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            new_role = st.selectbox("Role", ["analyst", "marketing_head"])
            add = st.form_submit_button("Add User")
            if add:
                if new_user and new_pass:
                    try:
                        users_df.loc[len(users_df)] = [new_user, new_pass, new_role]
                        safe_save_csv(users_df, USERS_CSV)
                        st.success("User added successfully.")
                        # reload cached data next run
                        st.experimental_singleton.clear()
                        st.experimental_data_editor  # no-op to avoid lint; keep behavior stable
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save users file: {e}")
                else:
                    st.error("Provide username and password.")

        st.subheader("Edit User Role")
        if not users_df.empty:
            selected_user = st.selectbox("Select User", users_df['username'].unique())
            new_role_edit = st.selectbox("New Role", ["analyst", "marketing_head", "admin"])
            if st.button("Update Role"):
                users_df.loc[users_df['username'] == selected_user, 'role'] = new_role_edit
                try:
                    safe_save_csv(users_df, USERS_CSV)
                    st.success("Role updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save users file: {e}")
        else:
            st.info("No users available to edit.")

    elif menu == "Manage Malls":
        st.subheader("Mall Management")
        try:
            malls_df = pd.read_csv(MALLS_CSV)
        except Exception:
            malls_df = pd.DataFrame(columns=["mall_id", "mall_name", "location"])

        st.dataframe(malls_df)

        with st.form("add_mall"):
            mall_id = st.number_input("Mall_ID", min_value=1, step=1)
            mall_name = st.text_input("Mall_name")
            mall_location = st.text_input("Mall_location")
            add_mall = st.form_submit_button("Add Mall")
            if add_mall:
                if mall_name:
                    try:
                        malls_df.loc[len(malls_df)] = [int(mall_id), mall_name.strip(), mall_location.strip()]
                        safe_save_csv(malls_df, MALLS_CSV)
                        st.success("Mall added.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save malls file: {e}")
                else:
                    st.error("Provide mall name.")


# ---------------- ANALYST DASHBOARD ----------------
def analyst_dashboard():
    if LOTTIE_SPARK is not None:
        try:
            st_lottie(LOTTIE_SPARK, height=60, key="analyst_spark")
        except Exception:
            pass

    st.header("Analyst Dashboard")
    data = load_data()
    if data.empty:
        st.error("Mall_Customers dataset not found at E://Mall_Customers.csv")
        return

    tab1, tab2, tab3 = st.tabs(["Raw Data", "Clustering", "Cluster Size"])
    with tab1:
        st.dataframe(data)

    with tab2:
        st.subheader("Clustering")
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if len(numeric_cols) < 2:
            numeric_cols = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
        if len(numeric_cols) < 2:
            st.error("Not enough numeric columns for clustering.")
        else:
            x_feature = st.selectbox("X-axis", numeric_cols, index=0)
            y_feature = st.selectbox("Y-axis", numeric_cols, index=1)
            k = st.slider("Number of Clusters", 2, 10, 5)

            X = data[[x_feature, y_feature]].copy()
            X = X.dropna().apply(pd.to_numeric, errors='coerce').dropna()
            if X.shape[0] < k:
                st.warning("Fewer data points than clusters; reduce k or clean data.")
            try:
                model = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = model.fit_predict(X)
                clustered = data.loc[X.index].copy()
                clustered['Cluster'] = labels.astype(int)
                fig = px.scatter(clustered, x=x_feature, y=y_feature, color='Cluster', title='Customer Segments', template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
                if st.checkbox("Show clustered table"):
                    st.dataframe(clustered[[x_feature, y_feature, 'Cluster']])
            except Exception as e:
                st.error(f"Clustering failed: {e}")

    with tab3:
        if 'Cluster' in data.columns:
            counts = data['Cluster'].value_counts().reset_index()
            counts.columns = ["Cluster", "Count"]
            fig = px.pie(counts, names='Cluster', values='Count', hole=0.5, title='Cluster Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No cluster column available. Run clustering in the Clustering tab.")

# ---------------- MARKETING DASHBOARD ----------------
def marketing_dashboard():
    if LOTTIE_SPARK is not None:
        try:
            st_lottie(LOTTIE_SPARK, height=60, key="marketing_spark")
        except Exception:
            pass

    st.header("Marketing Dashboard BY:🤖AI VISIONARIES")
    data = load_data()
    if data.empty:
        st.error("Mall_Customers dataset not found at E://Mall_Customers.csv")
        return

    # robustly find income and spending columns (original expected names preserved)
    def find_income_spend(df):
        inc = None
        spend = None
        for c in df.columns:
            lc = c.lower()
            if "annual" in lc and "income" in lc:
                inc = c
            if "spend" in lc or ("spending" in lc and "score" in lc):
                spend = c
        return inc, spend

    income_col, spend_col = find_income_spend(data)
    if not income_col or not spend_col:
        st.error("Could not locate income/spending columns. Expected names like 'Annual Income (IN INR)' and 'Spending Score (1-100)'.")
        st.write("Columns found:", data.columns.tolist())
        return

    X = data[[income_col, spend_col]].copy()
    X[income_col] = pd.to_numeric(X[income_col], errors='coerce')
    X[spend_col] = pd.to_numeric(X[spend_col], errors='coerce')
    X = X.dropna()

    k = st.slider("Number of clusters for marketing segmentation", 2, 8, 5)
    try:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X[[income_col, spend_col]])
        data.loc[X.index, 'Cluster'] = labels.astype(int)
    except Exception as e:
        st.error(f"Clustering error: {e}")
        return

    cluster_recommendations = {
        i: f"Recommendation for cluster {i}" for i in range(k)
    }

    st.subheader("Cluster Recommendations")
    for c in sorted(data.loc[X.index, 'Cluster'].unique()):
        rec_text = cluster_recommendations.get(int(c), "No suggestion")
        st.write(f"Cluster {c}: {rec_text}")

    # KPIs
    st.subheader("Advertising KPIs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ad Budget", "₹120,000", "+10%")
    col2.metric("Conversions", "8,500", "+5.4%")
    col3.metric("ROI Estimate", "₹230,000", "+18%")

    # Ad channel pie
    ad_channels = pd.DataFrame({
        "Channel": ["Facebook Ads", "Google Ads", "YouTube", "Print Media"],
        "Share": [40, 30, 20, 10]
    })
    fig = px.pie(ad_channels, names="Channel", values="Share", hole=0.4, title="Ad Channel Distribution")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🤖 AI Marketing Assistant by AI VISIONARY ")
    question = st.text_input("Ask for marketing advice:")
    if st.button("Get Suggestion"):
        q = question.lower()
        if "luxury" in q:
            st.success("Suggestion: Focus on high-income clusters and promote premium brands.")
        elif "discount" in q:
            st.success("Suggestion: Target price-sensitive clusters with discount coupons.")
        elif "bundle" in q:
            st.success("Suggestion: Target clusters that respond to bundled offers.")
        else:
            st.info("Suggestion: Try targeted social media campaigns")

# ---------------- MAIN ----------------
def main():
    if not st.session_state.logged_in:
        login_page()
        return

    # show header controls now (undo hide via css by rendering harmless markdown)
    st.markdown("<style>#MainMenu{visibility:visible;} footer{visibility:visible;} header{visibility:visible;}</style>", unsafe_allow_html=True)

    # sidebar with role info and navigation
    role = str(st.session_state.user_role).strip().lower()
    st.sidebar.markdown(f"**User:** {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {role}")

    # option menu choices preserve original labels
    choice = option_menu(
        "Mall Customer Dashboard",
        ["Admin", "Analyst", "Marketing", "Logout"],
        icons=["gear", "graph-up", "megaphone", "box-arrow-right"],
        menu_icon="shop",
        default_index=1,
    )

    # Role checks (preserve original behavior but normalize)
    if choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.rerun()
        return

    if choice == "Admin" and role == "admin":
        admin_dashboard()
    elif choice == "Analyst" and role == "analyst":
        analyst_dashboard()
    elif choice == "Marketing" and role in ("marketing_head", "marketing"):
        marketing_dashboard()
    else:
        st.warning("Access denied for this section. Please login with correct role or choose another section.")

if __name__ == "__main__":
    main()
