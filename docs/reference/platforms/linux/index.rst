=====
Linux
=====

.. _linux-prerequisites:

Prerequisites
=============

Briefcase requires installing Python 3.9+. You will also need a method for managing
virtual environments (such as ``venv``).

Packaging format
================

Briefcase supports packaging Linux apps as native system packages, as an `AppImage
<https://appimage.org>`__, and in `Flatpak <https://flatpak.org>`__ format.

The default output format for Linux is :doc:`system packages <./system>`.

.. toctree::
   :maxdepth: 1

   system
   appimage
   flatpak
