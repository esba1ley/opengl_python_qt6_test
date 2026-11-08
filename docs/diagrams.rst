Diagrams
========

How the program executes, drawn with `PlantUML <https://plantuml.com/>`__ from the code in ``src/``. The
diagrams are maintained by hand alongside the code; the sources are in
``docs/diagrams/``.

Structure
---------

.. uml:: diagrams/classes.puml
   :caption: Classes and the modules they depend on. ``CubeWidget`` owns the
             scene state and both renderers; the renderers read the state and
             never touch the widget or each other.

Startup
-------

.. uml:: diagrams/startup.puml
   :caption: From ``main()`` to the first frame. Qt creates the OpenGL context
             after ``show()``, which is when programs, textures and vertex
             buffers are built.

Painting a frame
----------------

.. uml:: diagrams/frame.puml
   :caption: One ``paintGL()`` call. Draw order is cube, sphere grid, axes,
             light dot, and only the grid draws without writing depth.

Mouse input
-----------

.. uml:: diagrams/mouse.puml
   :caption: Every mouse event becomes one ``SceneContext`` call followed by
             ``update()``; the widget keeps no scene state of its own.

Call graph
----------

.. uml:: diagrams/calls.puml
   :caption: Every function reachable from ``main()``, grouped by module.
             Solid arrows are calls; dotted arrows are repaints requested
             through Qt. ``selftest`` and the small texture helpers are left
             out.
