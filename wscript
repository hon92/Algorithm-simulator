#! /usr/bin/env python
# encoding: utf-8

import sys

VERSION='1.0.0'
APPNAME='Algorithm simulator'

top = '.'
out = 'build'
glade_files_dir = out + "/gui/dialogs/glade_dialogs/"
icons_files_dir = out + "/resources/icons/"

def options(opt):
    opt.load("python")
    opt.add_option("--dotpath",
                   action = "store",
                   default = None,
                   help = "set path for 'dot' program")

def configure(conf):
    conf.load("python")
    conf.check_python_version((2,7,10))
    conf.check_python_module("matplotlib")
    conf.check_python_module("gtk")
    conf.check_python_module("gtksourceview2")
    dotpath = conf.options.dotpath
    if dotpath:
        dot = conf.root.find_node(dotpath)
        if dot is None:
            conf.fatal("{0} not found".format(dotpath))

        dot_executable = None
        if sys.platform == "win32":
            dot_executable = "dot.exe*"
        elif sys.platform == "linux2":
            dot_executable = "dot"
        else:
            conf.fatal("Not supported os platform")

        dot_program = dot.ant_glob(dot_executable)
        if not dot_program:
            conf.fatal("'{0}' program was not found in '{1}'".format(dot_executable, dotpath))
        conf.msg("Checking for program 'dot'", dot)
    else:
        conf.find_program("dot")

def build(bld):
    bld(features='py', source=bld.path.ant_glob('sim/**/*.py'), install_from='.')
    bld(features='py', source=bld.path.ant_glob('gui/**/*.py'), install_from='.')
    bld(features='py', source=bld.path.ant_glob('misc/**/*.py'), install_from='.')

    glades_dir = bld.path.find_dir("gui/dialogs/glade_dialogs")
    icons_dir = bld.path.find_dir("resources/icons")

    bld.install_files(glade_files_dir, glades_dir.ant_glob("**/*.glade"))
    bld.install_files(icons_files_dir, icons_dir.ant_glob("**/*.png"))
