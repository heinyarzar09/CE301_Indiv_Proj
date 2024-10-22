# Import the create_app function from the app package
# This function will initialize and configure the Flask application instance
from app import create_app

# Create an instance of the Flask application by calling the create_app function
app = create_app()

# This block ensures that the application runs only if the script is executed directly
# The '__name__' variable is set to '__main__' when the script is run directly, not when imported
if __name__ == '__main__':
    # Run the Flask development server
    # 'debug=True' enables debug mode, which provides detailed error messages and auto-reloads the server on code changes
    # 'port=5005' specifies the port on which the server will listen for incoming requests
    app.run(debug=True, port=5005)
