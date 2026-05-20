def CORS(app=None, **kwargs):
    if app is not None:
        app.extensions = getattr(app, "extensions", {})
        app.extensions["cors"] = {"options": kwargs}
    return app
