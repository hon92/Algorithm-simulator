

if __name__ == '__main__':
    import sys
    from simulator.gui import app
    app = app.App(sys.argv[1:])
    app.run()