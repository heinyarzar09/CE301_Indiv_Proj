from app import create_app
from app.user_routes import user
from app.admin_routes import admin

app = create_app()

app.register_blueprint(user, url_prefix='/')
app.register_blueprint(admin, url_prefix='/admin')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
