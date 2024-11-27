# **CookMaster: A Gamified Social Cooking Platform**

CookMaster is a web-based platform designed to make cooking an enjoyable, engaging, and social experience. Users can share recipes, participate in cooking challenges, and manage credits that can be used for rewards or challenges.

---

## **Getting Started**

Follow the instructions below to set up the project and run it locally.

### **Prerequisites**

Before starting, ensure you have the following installed:
- **Python**: Version 3.8 or higher
- **pip**: Python package installer

---

### **Installation**

Clone the repository and install the required dependencies:

```bash
# Clone the repository
git clone https://github.com/heinyarzar09/CE301_Indiv_Proj.git

# Navigate to the project directory
cd CE301_Indiv_Proj

# Install dependencies
pip install -r requirements.txt
```

---

### **Running the Application**

Start the application locally:

```bash
python run.py
```

The application will run on [http://localhost:5005], where you can interact with it.

---

## **Features**

- **User Registration and Login**: A secure system to manage user sessions.
- **Recipe Sharing**: Post, share, and view recipes with others.
- **Cooking Challenges**: Participate in exciting timed challenges to earn credits.
- **Credit Management**: Earn, spend, and withdraw credits via an intuitive system.
- **Admin Dashboard**: Manage users, challenges, and site settings with admin privileges.

---

## **Code Structure**

| File/Directory          | Description                                                |
|-------------------------|------------------------------------------------------------|
| **`__init__.py`**       | Initializes the Flask application and configurations.      |
| **`models.py`**         | Defines database models for Users, Posts, Challenges, etc. |
| **`forms.py`**          | Handles forms for user registration, login, and posts.     |
| **`user_routes.py`**    | Manages routes related to user interactions.               |
| **`admin_routes.py`**   | Handles admin-specific operations and routes.              |
| **`utils.py`**          | Utility functions to support core functionalities.         |

---

## **Authors**

- **Hein Yar Zar**  
  GitHub: [HeinYarZar09](https://github.com/heinyarzar09)

---
