import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans

st.set_page_config(page_title="Mall Customer Dashboard", layout="centered")

@st.cache_data
def load_users():
    return pd.read_csv("E://user.csv")

@st.cache_data
def load_data():
    return pd.read_csv("E://Mall_Customers.csv")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = ""
    st.session_state.username = ""

users = load_users()

# LOGIN SECTION
if not st.session_state.logged_in:
    st.sidebar.title("Login Panel")
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")

    if login_btn:
        user = users[(users['username'] == username_input) & (users['password'] == password_input)]

        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.user_role = user.iloc[0]['role']
            st.session_state.username = user.iloc[0]['username']
            st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.user_role})")
        else:
            st.sidebar.error("Invalid username or password")

# LOGGED IN SECTION
if st.session_state.logged_in:
    st.sidebar.write(f"Welcome: **{st.session_state.username}**")
    st.sidebar.write(f"Role: `{st.session_state.user_role}`")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.rerun()

    # ROLE-BASED DASHBOARD
    role = st.session_state.user_role

    if role == "admin":
        st.title("Admin Dashboard")
        menu = st.selectbox("Choose Action", ["Manage Users", "Manage Malls"])

        if menu == "Manage Users":
            users_df = load_users()

            st.subheader("User List")
            st.dataframe(users_df)

            st.subheader("Add New User")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            new_role = st.selectbox("Role", ["analyst", "marketing_head"])

            if st.button("Add User"):
                if new_user and new_pass:
                    users_df.loc[len(users_df)] = [new_user, new_pass, new_role]
                    users_df.to_csv("E://user.csv", index=False)
                    st.success("User added successfully!")

            st.subheader("Edit User Role")
            selected_user = st.selectbox("Select User", users_df['username'].unique())
            new_role_edit = st.selectbox("New Role", ["analyst", "marketing_head", "admin"])
            if st.button("Update Role"):
                users_df.loc[users_df['username'] == selected_user, 'role'] = new_role_edit
                users_df.to_csv("E://user.csv", index=False)
                st.success("Role updated!")

        elif menu == "Manage Malls":
            st.subheader("Mall Management")
            try:
                malls_df = pd.read_csv("E:/mall_brances.csv")
            except:
                malls_df = pd.DataFrame(columns=["mall_id", "mall_name", "location"])

            st.dataframe(malls_df)

            mall_id = st.number_input("Mall_ID", min_value=1, step=1)
            mall_name = st.text_input("Mall_name")
            mall_location = st.text_input("mall_location")
            if st.button("Add Mall"):
                malls_df.loc[len(malls_df)] = [mall_id, mall_name, mall_location]
                malls_df.to_csv("E:/malls.csv", index=False)
                st.success("Mall added!")

    elif role == "analyst":
        st.title("Analyst Dashboard")
        data = load_data()

        if st.checkbox("Show Raw Data"):
            st.dataframe(data)

        st.subheader("Clustering")
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns.tolist()
        x_feature = st.selectbox("X-axis", numeric_cols, index=0)
        y_feature = st.selectbox("Y-axis", numeric_cols, index=1)
        k = st.slider("Number of Clusters", 2, 10, 5)

        X = data[[x_feature, y_feature]]
        model = KMeans(n_clusters=k, random_state=42)
        data['Cluster'] = model.fit_predict(X)

        if st.checkbox("Show Clustered Data"):
            st.dataframe(data[[x_feature, y_feature, 'Cluster']])

        fig, ax = plt.subplots()
        sns.scatterplot(data=data, x=x_feature, y=y_feature, hue="Cluster", palette="Set2", s=100, ax=ax)
        st.pyplot(fig)

    elif role == "marketing_head":
        st.title("Marketing Dashboard")
        data = load_data()

        X = data[["Annual Income (IN INR)", "Spending Score (1-100)"]]
        model = KMeans(n_clusters=5, random_state=42)
        data['Cluster'] = model.fit_predict(X)

        cluster_recommendations = {
            0: "Offer discounts and entry coupons",
            1: "Promote luxury products",
            2: "Bundle casual offers",
            3: "Buy-one-get-one deals",
            4: "Banking and investment partnerships"
        }

        for c in sorted(data['Cluster'].unique()):
            st.write(f"Cluster {c}: {cluster_recommendations.get(c, 'No suggestion')}")

        st.bar_chart(data['Cluster'].value_counts().sort_index())
                # 📣 Advertising Insights Section
        st.subheader("📣 Advertising Overview")
        st.markdown("Tracking our promotional campaigns and their impact on mall traffic.")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Ad Budget", "₹1,20,000", "+10%")
            st.metric("Reach (People)", "1.2M", "+8%")
            st.metric("Social Media CTR", "4.5%", "+0.3%")

        with col2:
            st.metric("Conversions", "8,500", "+5.4%")
            st.metric("Campaigns Run", "12", "+2 new")
            st.metric("ROI Estimate", "₹2.3L", "+18%")

        # 📊 Pie chart for Advertising Channels
        labels = ['Facebook Ads', 'Google Ads', 'YouTube', 'Print Media']
        sizes = [40, 30, 20, 10]
        colors = ['#FF9999', '#66B3FF', '#99FF99', '#FFD700']

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)