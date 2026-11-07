Test suite
==========

One page per file in ``tests/``, generated from the docstrings. Each test's
docstring says what it checks and, in a second paragraph marked **WHY:**,
why the suite needs it: the bug it would catch, or the convention it pins. The fixtures
the GL tests share are on the ``conftest`` page.

.. toctree::
   :maxdepth: 1

   conftest
   test_config
   test_conftest
   test_context
   test_cube
   test_geometry
   test_gl_utils
   test_main
   test_overlay
   test_selftest
   test_shaders
   test_textures
   test_widget
