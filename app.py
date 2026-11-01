import os
from flask import Flask, session, g, render_template, jsonify
from config import Config
from database import init_db, close_db
from translations import get_text, TRANSLATIONS

# Import blueprints
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.scanner_routes import scanner_bp
from routes.inventory_routes import inventory_bp
from routes.sales_routes import sales_bp
from routes.recommendations_routes import recommendations_bp
from routes.analytics_routes import analytics_bp
from routes.chatbot_routes import chatbot_bp
from routes.connect_routes import connect_bp

def create_app(test_config=None):
    project_root = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    app.config.from_object(Config)
    
    if test_config:
        app.config.update(test_config)
        
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Teardown database connection
    app.teardown_appcontext(close_db)
    
    # Initialize DB tables & seed demo shop
    with app.app_context():
        init_db(app)
        
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scanner_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(connect_bp)
    
    # Global context processors for Jinja2
    @app.context_processor
    def inject_globals():
        lang = session.get('lang', 'en')
        return {
            'current_lang': lang,
            'shop_name': session.get('shop_name', ''),
            'username': session.get('username', ''),
            'is_logged_in': ('user_id' in session),
            't': lambda key, **kwargs: get_text(key, lang=lang, **kwargs)
        }
        
    # Template filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            val_f = float(val)
            if val_f.is_integer():
                return f"₹{int(val_f)}"
            return f"₹{val_f:.2f}"
        except Exception:
            return f"₹{val}"
            
    # API to fetch full translation dictionary for client-side JavaScript
    @app.route('/api/translations')
    def api_translations():
        lang = session.get('lang', 'en')
        return jsonify({
            "current_lang": lang,
            "strings": TRANSLATIONS.get(lang, TRANSLATIONS['en']),
            "all_languages": {
                "en": TRANSLATIONS['en'],
                "hi": TRANSLATIONS['hi'],
                "mr": TRANSLATIONS['mr']
            }
        })

    # Friendly error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_title="404 - Page Not Found", error_msg="The requested page does not exist."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('base.html', error_title="500 - Server Error", error_msg="Something went wrong on our end. Please try again."), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Listen on all interfaces so mobile phones on the local WiFi can also access the app!
    app.run(host='0.0.0.0', port=5000, debug=False)
