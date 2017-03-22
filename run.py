

if __name__ == '__main__':
    import sys
    from src.gui import app
    from src.gui import settings
    settings.init()
    app = app.App(sys.argv[1:])
    app.run()