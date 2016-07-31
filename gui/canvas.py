import gtk
import cairo
import math

class Canvas(gtk.DrawingArea):
    DASH = [10,10,10,10,10]

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("configure_event", self.on_configure)
        self.connect("expose_event", self.on_expose)
        self.zoom = 1.0
        self.line_width = 2
        self.r = 0
        self.g = 0
        self.b = 0
        self.surface = None

    def _get_context(self):
        ctx = cairo.Context(self.surface)
        ctx.set_line_width(self.line_width)
        ctx.set_source_rgb(self.r, self.g, self.b)
        ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        return ctx

    def set_zoom(self, zoom):
        self.zoom = zoom

    def get_zoom(self):
        return self.zoom
    
    def set_line_width(self, s = 2):
        self.line_width = s

    def set_color(self, r = 0.0, g = 0.0, b = 0.0):
        self.r = r / 255.0
        self.b = b / 255.0
        self.g = g / 255.0

    def repaint(self):
        self.queue_draw_area(0, 0, self.allocation.width, self.allocation.height)

    def on_configure(self, w, e):
        width = w.allocation.width
        height = w.allocation.height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)

    def on_expose(self, w, e):
        cr = w.window.cairo_create()
        cr.scale(self.zoom, self.zoom)
        cr.set_source_surface(self.surface, 0, 0)
        cr.paint()

    def draw_rectangle(self, x, y, w, h, fill = False):
        ctx = self._get_context()
        ctx.rectangle(x, y, w, h)
        if fill:
            ctx.fill()
        else:
            ctx.stroke()

    def draw_text(self, x, y, text):
        ctx = self._get_context()
        ctx.move_to(x, y)
        ctx.show_text(text)
        ctx.stroke()

    def draw_centered_text(self, x, y, text):
        ctx = self._get_context()
        t = ctx.text_extents(text)
        self.draw_text(x - t[2] / 2, y + t[3] / 2, text)

    def draw_lines(self, points):
        ctx = self._get_context()
        ctx.move_to(points[0], points[1])
        for i in xrange(2, len(points), 2):
            ctx.line_to(points[i], points[i + 1])
        ctx.stroke()

    def draw_line(self, x1, y1, x2, y2):
        ctx = self._get_context()
        ctx.move_to(x1, y1)
        ctx.line_to(x2,y2)
        ctx.stroke()

    def draw_polygon(self, points, fill = False):
        ctx = self._get_context()
        ctx.move_to(points[0][0], points[0][1])
        for i in xrange(1, len(points)):
            ctx.line_to(points[i][0], points[i][1])
        ctx.move_to(points[-1][0], points[-1][1])

        if fill:
            ctx.fill()
        else:
            ctx.stroke()

    def draw_path(self, path, dashed):
        ctx = self._get_context()
        if dashed is True:
            ctx.set_dash(self.DASH, 0)
        ctx.move_to(path[0][0], path[0][1])
        p = (len(path) - 1) / 3
        i = 1
        for _ in xrange(p):
            ctx.curve_to(path[i][0], path[i][1],
                         path[i + 1][0], path[i + 1][1],
                         path[i + 2][0], path[i + 2][1],
                         )
            i += 3
        ctx.stroke()

    def draw_arrow(self, x1, y1, x2, y2):
        ctx = self._get_context()
        ctx.save()
        ctx.translate(x2, y2)
        ctx.rotate(math.atan2(y2 - y1, x2 - x1))
        ctx.move_to(0, 0)
        ctx.line_to(-10,10)
        ctx.move_to(0,0)
        ctx.line_to(-10, -10)
        ctx.restore()
        ctx.stroke()

    def get_intersection_point(self, x1, y1, x2, y2, rect):
        lines = [(rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"]),
                 (rect["x"], rect["y"], rect["x"], rect["y"] + rect["height"] / 2),
                 (rect["x"], rect["y"] + rect["height"] / 2, rect["x"] + rect["width"], rect["y"] + rect["height"] / 2),
                 (rect["x"] + rect["width"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"] / 2)]
        
        for x1x,y1x,x2x,y2x in lines:
            x3 = x1x
            y3 = y1x
            x4 = x2x
            y4 = y2x
            
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            if denom == 0.0:
                if x2 == x1:
                    return (x2, y4)
                if y1 == y2 and x2 > x1:
                    return (x4, y2);
                if y1 == y2 and x1 > x2:
                    return (x3, y2);
                return (x2, y4);
            ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
            ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;
            if ua >= 0.0 and ua <= 1.0 and ub >= 0.0 and ub <= 1.0:
                # Get the intersection point.
                return ((x1 + ua * (x2 - x1)), (y1 + ua * (y2 - y1)));
        return (x2,y2)

    def dispose(self):
        self.surface = None