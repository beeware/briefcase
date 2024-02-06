===============
Release History
===============

.. towncrier release notes start

0.3.17 (2024-02-06)
===================

Features
--------

* Android apps are now able to customize the libraries included in the app at build time. (`#485 <https://github.com/beeware/briefcase/issues/485>`__)
* App permissions can now be declared as part of an app's configuration. (`#547 <https://github.com/beeware/briefcase/issues/547>`__)
* The ``-C``/``--config`` option can now be used to override app settings from the command line. (`#1115 <https://github.com/beeware/briefcase/issues/1115>`__)
* The verbosity flag, ``-v``, was expanded to support three levels of logging verbosity. (`#1501 <https://github.com/beeware/briefcase/issues/1501>`__)
* Briefcase now supports GUI bootstrap plugins to customize how new projects are created. (`#1524 <https://github.com/beeware/briefcase/issues/1524>`__)
* GitPython's debug logging is now included in deep debug output. (`#1529 <https://github.com/beeware/briefcase/issues/1529>`__)
* RCEdit v2.0.0 is now used to build Windows apps. Run ``briefcase upgrade`` to use this latest version. (`#1543 <https://github.com/beeware/briefcase/issues/1543>`__)
* The Flatpak runtimes for new projects were updated. ``org.freedesktop.Platform`` will now default to 23.08; ``org.gnome.Platform`` will now default to 45; and ``org.kde.Platform`` will now default to 6.6. (`#1545 <https://github.com/beeware/briefcase/issues/1545>`__)
* When creating new projects with the ``briefcase new`` command, project configuration overrides can be specified via the ``-Q`` command line argument. For instance, a specific license can be specified with ``-Q "license=MIT license"``. (`#1552 <https://github.com/beeware/briefcase/issues/1552>`__)
* New virtual devices for the Android emulator are created using the Pixel 7 Pro skin. (`#1554 <https://github.com/beeware/briefcase/issues/1554>`__)
* The web server for running static web projects now falls back to a system allocated port if the requested port is already in use. (`#1561 <https://github.com/beeware/briefcase/issues/1561>`__)
* Flatpaks are now created with permissions to access the GPU and sound devices. (`#1563 <https://github.com/beeware/briefcase/issues/1563>`__)
* AppImages can now be built for the ARM architecture. (`#1564 <https://github.com/beeware/briefcase/issues/1564>`__)
* Apps can now specify a primary color (for both light and dark modes), and an accent color. If the platform allows apps to customize color use, these colors will be used to style the app's presentation. (`#1566 <https://github.com/beeware/briefcase/issues/1566>`__)
* The version of PursuedPyBear for new projects was bumped from 1.1 to 3.2.0. (`#1592 <https://github.com/beeware/briefcase/issues/1592>`__)
* Python 3.12 is now supported on Android. (`#1596 <https://github.com/beeware/briefcase/issues/1596>`__)
* Android apps can now specify the base theme used to style the application. (`#1610 <https://github.com/beeware/briefcase/issues/1610>`__)
* The Java JDK was upgraded from 17.0.8.1+1 to 17.0.10+7. Run ``briefcase upgrade java`` to upgrade existing Briefcase installations. (`#1611 <https://github.com/beeware/briefcase/issues/1611>`__)
* When the Android emulator fails to start up properly, users are now presented with additional resources to help resolve any issues. (`#1630 <https://github.com/beeware/briefcase/issues/1630>`__)


Bugfixes
--------

* When a custom Briefcase template from a git repository is used to create an app, Briefcase now ensures that git repository is always used. (`#1158 <https://github.com/beeware/briefcase/issues/1158>`__)
* The filter for iOS build warnings was improved to catch messages from Xcode 15.0.1. (`#1507 <https://github.com/beeware/briefcase/issues/1507>`__)
* When merging dependencies on macOS, file permissions are now preserved. (`#1510 <https://github.com/beeware/briefcase/issues/1510>`__)
* ``flatpak-builder`` 1.3+ can now be correctly identified. (`#1513 <https://github.com/beeware/briefcase/issues/1513>`__)
* The BeeWare icon of Brutus is now used as the runtime icon for new projects created with PyGame. (`#1532 <https://github.com/beeware/briefcase/issues/1532>`__)
* Linux System RPM packaging for openSUSE Tumbleweed no longer errors with ``FileNotFoundError``. (`#1595 <https://github.com/beeware/briefcase/issues/1595>`__)
* Any ANSI escape sequences or console control codes are now stripped in all output captured in the Briefcase log file. (`#1604 <https://github.com/beeware/briefcase/issues/1604>`__)
* The detection of physical Android devices on macOS was made more resilient. (`#1627 <https://github.com/beeware/briefcase/issues/1627>`__)


Backward Incompatible Changes
-----------------------------

* The use of AppImage as an output format now generates a warning. (`#1500 <https://github.com/beeware/briefcase/issues/1500>`__)
* Support for creating new projects using PySide2 has been removed. Briefcase's release testing will no longer explicitly verify compatibility with PySide2. (`#1524 <https://github.com/beeware/briefcase/issues/1524>`__)
* The Flatpak build process no longer strips binaries included in third-party (e.g. PyPI) packages that are bundled with the app. (`#1540 <https://github.com/beeware/briefcase/issues/1540>`__)
* New projects will now use ``manylinux_2_28`` instead of ``manylinux2014`` to create AppImages in Docker. (`#1564 <https://github.com/beeware/briefcase/issues/1564>`__)
* It is highly recommended that Android applications add a definition for ``build_gradle_dependencies`` to their app configuration. A default value will be used if this option is not explicitly provided. Refer to `the Android documentation <https://briefcase.readthedocs.io/en/latest/reference/platforms/android/gradle.html#build-gradle-dependencies>`__ for the default value that will be used. (`#1610 <https://github.com/beeware/briefcase/issues/1610>`__)


Documentation
-------------

* The common options available to every command have now been documented. (`#1517 <https://github.com/beeware/briefcase/issues/1517>`__)


Misc
----

* `#1504 <https://github.com/beeware/briefcase/issues/1504>`__, `#1505 <https://github.com/beeware/briefcase/issues/1505>`__, `#1506 <https://github.com/beeware/briefcase/issues/1506>`__, `#1515 <https://github.com/beeware/briefcase/issues/1515>`__, `#1516 <https://github.com/beeware/briefcase/issues/1516>`__, `#1518 <https://github.com/beeware/briefcase/issues/1518>`__, `#1519 <https://github.com/beeware/briefcase/issues/1519>`__, `#1526 <https://github.com/beeware/briefcase/issues/1526>`__, `#1527 <https://github.com/beeware/briefcase/issues/1527>`__, `#1533 <https://github.com/beeware/briefcase/issues/1533>`__, `#1534 <https://github.com/beeware/briefcase/issues/1534>`__, `#1535 <https://github.com/beeware/briefcase/issues/1535>`__, `#1536 <https://github.com/beeware/briefcase/issues/1536>`__, `#1538 <https://github.com/beeware/briefcase/issues/1538>`__, `#1541 <https://github.com/beeware/briefcase/issues/1541>`__, `#1548 <https://github.com/beeware/briefcase/issues/1548>`__, `#1549 <https://github.com/beeware/briefcase/issues/1549>`__, `#1550 <https://github.com/beeware/briefcase/issues/1550>`__, `#1551 <https://github.com/beeware/briefcase/issues/1551>`__, `#1555 <https://github.com/beeware/briefcase/issues/1555>`__, `#1556 <https://github.com/beeware/briefcase/issues/1556>`__, `#1557 <https://github.com/beeware/briefcase/issues/1557>`__, `#1560 <https://github.com/beeware/briefcase/issues/1560>`__, `#1562 <https://github.com/beeware/briefcase/issues/1562>`__, `#1567 <https://github.com/beeware/briefcase/issues/1567>`__, `#1568 <https://github.com/beeware/briefcase/issues/1568>`__, `#1569 <https://github.com/beeware/briefcase/issues/1569>`__, `#1571 <https://github.com/beeware/briefcase/issues/1571>`__, `#1575 <https://github.com/beeware/briefcase/issues/1575>`__, `#1576 <https://github.com/beeware/briefcase/issues/1576>`__, `#1579 <https://github.com/beeware/briefcase/issues/1579>`__, `#1582 <https://github.com/beeware/briefcase/issues/1582>`__, `#1585 <https://github.com/beeware/briefcase/issues/1585>`__, `#1586 <https://github.com/beeware/briefcase/issues/1586>`__, `#1589 <https://github.com/beeware/briefcase/issues/1589>`__, `#1590 <https://github.com/beeware/briefcase/issues/1590>`__, `#1597 <https://github.com/beeware/briefcase/issues/1597>`__, `#1606 <https://github.com/beeware/briefcase/issues/1606>`__, `#1607 <https://github.com/beeware/briefcase/issues/1607>`__, `#1613 <https://github.com/beeware/briefcase/issues/1613>`__, `#1614 <https://github.com/beeware/briefcase/issues/1614>`__, `#1615 <https://github.com/beeware/briefcase/issues/1615>`__, `#1618 <https://github.com/beeware/briefcase/issues/1618>`__, `#1621 <https://github.com/beeware/briefcase/issues/1621>`__, `#1622 <https://github.com/beeware/briefcase/issues/1622>`__, `#1623 <https://github.com/beeware/briefcase/issues/1623>`__, `#1624 <https://github.com/beeware/briefcase/issues/1624>`__, `#1628 <https://github.com/beeware/briefcase/issues/1628>`__, `#1632 <https://github.com/beeware/briefcase/issues/1632>`__, `#1633 <https://github.com/beeware/briefcase/issues/1633>`__


0.3.16 (2023-10-20)
===================

Features
--------

* Support for less common environments, such as Linux on ARM, has been improved. Error messages for unsupported platforms are now more accurate. (`#1360 <https://github.com/beeware/briefcase/pull/1360>`__)
* Tool verification for Java, Android SDK, and WiX have been improved to provide more informative errors and debug logging. (`#1382 <https://github.com/beeware/briefcase/pull/1382>`__)
* A super verbose logging mode was added (enabled using ``-vv``). This turns on all Briefcase internal logging, but also enables verbose logging for all the third-party tools that Briefcase invokes. (`#1384 <https://github.com/beeware/briefcase/issues/1384>`__)
* Briefcase now uses Android SDK Command-Line Tools v9.0. If an externally-managed Android SDK is being used, it must provide this version of Command-Line Tools. Use the SDK Manager in Android Studio to ensure it is installed. (`#1397 <https://github.com/beeware/briefcase/pull/1397>`__)
* Support for OpenSuSE Linux distributions was added. (`#1416 <https://github.com/beeware/briefcase/issues/1416>`__)
* iOS apps are no longer rejected by the iOS App Store for packaging reasons. (`#1439 <https://github.com/beeware/briefcase/pull/1439>`__)
* The Java JDK version was upgraded to 17.0.8.1+1. (`#1462 <https://github.com/beeware/briefcase/pull/1462>`__)
* macOS apps can now be configured to produce single platform binaries, or binaries that will work on both x86_64 and ARM64. (`#1482 <https://github.com/beeware/briefcase/issues/1482>`__)


Bugfixes
--------

* Build warnings caused by bugs in Xcode that can be safely ignored are now filtered out of visible output. (`#377 <https://github.com/beeware/briefcase/issues/377>`__)
* The run command now ensures Android logging is shown when the datetime on the device is different from the host machine. (`#1146 <https://github.com/beeware/briefcase/issues/1146>`__)
* Briefcase will detect if you attempt to launch an Android app on a device whose OS doesn't meet minimum version requirements. (`#1157 <https://github.com/beeware/briefcase/issues/1157>`__)
* macOS apps are now guaranteed to be universal binaries, even when dependencies only provide single-architecture binary wheels. (`#1217 <https://github.com/beeware/briefcase/issues/1217>`__)
* The ability to build AppImages in Docker on macOS was restored. (`#1352 <https://github.com/beeware/briefcase/issues/1352>`__)
* Error reporting has been improved when the target Docker image name is invalid. (`#1368 <https://github.com/beeware/briefcase/issues/1368>`__)
* Creating Debian packages no longer fails due to a permission error for certain ``umask`` values (such as ``0077``). (`#1369 <https://github.com/beeware/briefcase/issues/1369>`__)
* Inside of Docker containers, the Briefcase data directory is now mounted at ``/briefcase`` instead of ``/home/brutus/.cache/briefcase``. (`#1374 <https://github.com/beeware/briefcase/issues/1374>`__)
* The console output from invoking Python via a subprocess call is now properly decoded as UTF-8. (`#1407 <https://github.com/beeware/briefcase/issues/1407>`__)
* The command line arguments used to configure the Python environment for ``briefcase dev`` no longer leak into the runtime environment on macOS. (`#1413 <https://github.com/beeware/briefcase/pull/1413>`__)


Backward Incompatible Changes
-----------------------------

* AppImage packaging requires a recent release of LinuxDeploy to continue creating AppImages. Run ``briefcase upgrade linuxdeploy`` to install the latest version. (`#1361 <https://github.com/beeware/briefcase/issues/1361>`__)
* The size of iOS splash images have changed. iOS apps should now provide 800px, 1600px and 2400px images (previously, this as 1024px, 2048px and 3072px). This is because iOS 14 added a hard limit on the size of image resources. (`#1371 <https://github.com/beeware/briefcase/pull/1371>`__)
* Support for AppImage has been reduced to "best effort". We will maintain unit test coverage for the AppImage backend, but we no longer build AppImages as part of our release process. We will accept bug reports related to AppImage support, and we will merge PRs that address AppImage support, but the core team no longer considers addressing AppImage bugs a priority, and discourages the use of AppImage for new projects. (`#1449 <https://github.com/beeware/briefcase/pull/1449>`__)


Documentation
-------------

* Documentation on the process of retrieving certificate identities on macOS and Windows was improved. (`#1473 <https://github.com/beeware/briefcase/pull/1473>`__)


Misc
----

* `#1136 <https://github.com/beeware/briefcase/issues/1136>`__, `#1290 <https://github.com/beeware/briefcase/pull/1290>`__, `#1363 <https://github.com/beeware/briefcase/pull/1363>`__, `#1364 <https://github.com/beeware/briefcase/pull/1364>`__, `#1365 <https://github.com/beeware/briefcase/pull/1365>`__, `#1372 <https://github.com/beeware/briefcase/pull/1372>`__, `#1375 <https://github.com/beeware/briefcase/pull/1375>`__, `#1376 <https://github.com/beeware/briefcase/pull/1376>`__, `#1379 <https://github.com/beeware/briefcase/issues/1379>`__, `#1388 <https://github.com/beeware/briefcase/pull/1388>`__, `#1394 <https://github.com/beeware/briefcase/pull/1394>`__, `#1395 <https://github.com/beeware/briefcase/pull/1395>`__, `#1396 <https://github.com/beeware/briefcase/pull/1396>`__, `#1398 <https://github.com/beeware/briefcase/pull/1398>`__, `#1400 <https://github.com/beeware/briefcase/pull/1400>`__, `#1401 <https://github.com/beeware/briefcase/pull/1401>`__, `#1402 <https://github.com/beeware/briefcase/pull/1402>`__, `#1403 <https://github.com/beeware/briefcase/pull/1403>`__, `#1408 <https://github.com/beeware/briefcase/pull/1408>`__, `#1409 <https://github.com/beeware/briefcase/pull/1409>`__, `#1410 <https://github.com/beeware/briefcase/pull/1410>`__, `#1411 <https://github.com/beeware/briefcase/issues/1411>`__, `#1412 <https://github.com/beeware/briefcase/pull/1412>`__, `#1418 <https://github.com/beeware/briefcase/pull/1418>`__, `#1419 <https://github.com/beeware/briefcase/pull/1419>`__, `#1420 <https://github.com/beeware/briefcase/pull/1420>`__, `#1421 <https://github.com/beeware/briefcase/pull/1421>`__, `#1427 <https://github.com/beeware/briefcase/pull/1427>`__, `#1429 <https://github.com/beeware/briefcase/issues/1429>`__, `#1431 <https://github.com/beeware/briefcase/issues/1431>`__, `#1433 <https://github.com/beeware/briefcase/pull/1433>`__, `#1435 <https://github.com/beeware/briefcase/pull/1435>`__, `#1436 <https://github.com/beeware/briefcase/pull/1436>`__, `#1437 <https://github.com/beeware/briefcase/pull/1437>`__, `#1438 <https://github.com/beeware/briefcase/pull/1438>`__, `#1442 <https://github.com/beeware/briefcase/pull/1442>`__, `#1443 <https://github.com/beeware/briefcase/pull/1443>`__, `#1444 <https://github.com/beeware/briefcase/pull/1444>`__, `#1445 <https://github.com/beeware/briefcase/pull/1445>`__, `#1446 <https://github.com/beeware/briefcase/pull/1446>`__, `#1447 <https://github.com/beeware/briefcase/pull/1447>`__, `#1448 <https://github.com/beeware/briefcase/pull/1448>`__, `#1454 <https://github.com/beeware/briefcase/pull/1454>`__, `#1455 <https://github.com/beeware/briefcase/pull/1455>`__, `#1456 <https://github.com/beeware/briefcase/pull/1456>`__, `#1457 <https://github.com/beeware/briefcase/pull/1457>`__, `#1464 <https://github.com/beeware/briefcase/pull/1464>`__, `#1465 <https://github.com/beeware/briefcase/pull/1465>`__, `#1466 <https://github.com/beeware/briefcase/pull/1466>`__, `#1470 <https://github.com/beeware/briefcase/pull/1470>`__, `#1474 <https://github.com/beeware/briefcase/pull/1474>`__, `#1476 <https://github.com/beeware/briefcase/pull/1476>`__, `#1477 <https://github.com/beeware/briefcase/pull/1477>`__, `#1478 <https://github.com/beeware/briefcase/pull/1478>`__, `#1481 <https://github.com/beeware/briefcase/issues/1481>`__, `#1485 <https://github.com/beeware/briefcase/pull/1485>`__, `#1486 <https://github.com/beeware/briefcase/pull/1486>`__, `#1487 <https://github.com/beeware/briefcase/pull/1487>`__, `#1488 <https://github.com/beeware/briefcase/pull/1488>`__, `#1489 <https://github.com/beeware/briefcase/pull/1489>`__, `#1490 <https://github.com/beeware/briefcase/pull/1490>`__, `#1492 <https://github.com/beeware/briefcase/pull/1492>`__, `#1494 <https://github.com/beeware/briefcase/pull/1494>`__


0.3.15 (2023-07-10)
===================

Features
--------

* Windows apps can now be packaged as simple ZIP files. (`#457 <https://github.com/beeware/briefcase/issues/457>`__)
* An Android SDK specified in ``ANDROID_HOME`` is respected now and will take precedence over the setting of ``ANDROID_SDK_ROOT``. (`#463 <https://github.com/beeware/briefcase/issues/463>`__)
* Android support was upgraded to use Java 17 for builds. (`#1065 <https://github.com/beeware/briefcase/issues/1065>`__)
* On Linux, Docker Desktop and rootless Docker are now supported. (`#1083 <https://github.com/beeware/briefcase/issues/1083>`__)
* The company/author name in the installation path for Windows MSI installers is now optional. (`#1199 <https://github.com/beeware/briefcase/issues/1199>`__)
* macOS code signing is now multi-threaded (and therefore much faster!) (`#1201 <https://github.com/beeware/briefcase/issues/1201>`__)
* Briefcase will now honor PEP-621 project fields where they map to Briefcase configuration items. (`#1203 <https://github.com/beeware/briefcase/issues/1203>`__)

Bugfixes
--------

* XML compatibility warnings generated by the Android build have been cleaned up. (`#827 <https://github.com/beeware/briefcase/issues/827>`__)
* Non ASCII characters provided in the ``briefcase new`` wizard are quoted before being put into ``pyproject.toml``. (`#1011 <https://github.com/beeware/briefcase/issues/1011>`__)
* Requests to the web server are now recorded in the log file. (`#1090 <https://github.com/beeware/briefcase/issues/1090>`__)
* An "Invalid Keystore format" error is no longer raised when signing an app if the local Android keystore was generated with a recent version of Java. (`#1112 <https://github.com/beeware/briefcase/issues/1112>`__)
* Content before a closing square bracket (``]``) or ``.so)`` is no longer stripped by the macOS and iOS log filter. (`#1179 <https://github.com/beeware/briefcase/issues/1179>`__)
* The option to run Linux system packages through Docker was removed. (`#1207 <https://github.com/beeware/briefcase/issues/1207>`__)
* Error handling for incomplete or corrupted Github clones of templates has been improved. (`#1210 <https://github.com/beeware/briefcase/pull/1210>`__)
* Application/Bundle IDs are normalized to replace underscores with dashes when possible (`#1234 <https://github.com/beeware/briefcase/pull/1234>`__)
* Filenames and directories in RPM package definitions are quoted in order to include filenames that include white space. (`#1236 <https://github.com/beeware/briefcase/issues/1236>`__)
* Briefcase will no longer display progress bars if the ``FORCE_COLOR`` environment variable is set. (`#1267 <https://github.com/beeware/briefcase/pull/1267>`__)
* When creating a new Briefcase project, the header line in ``pyproject.toml`` now contains the version of Briefcase instead of "Unknown". (`#1276 <https://github.com/beeware/briefcase/pull/1276>`__)
* Android logs no longer include timestamp and PID, making them easier to read on narrow screens. (`#1286 <https://github.com/beeware/briefcase/pull/1286>`__)
* An warning is no longer logged if the Java identified by macOS is not usable by Briefcase. (`#1305 <https://github.com/beeware/briefcase/issues/1305>`__)
* Incompatibilities with Cookiecutter 2.2.0 have been resolved. (`#1347 <https://github.com/beeware/briefcase/issues/1347>`__)

Backward Incompatible Changes
-----------------------------

* Names matching modules in the Python standard library, and ``main``, can no longer be used as an application name. (`#853 <https://github.com/beeware/briefcase/issues/853>`__)
* The ``--no-sign`` option for packaging was removed. Briefcase will now prompt for a signing identity during packaging, falling back to adhoc/no signing as a default where possible. (`#865 <https://github.com/beeware/briefcase/issues/865>`__)
* The version of OpenJDK for Java was updated from 8 to 17. Any Android apps generated on previous versions of Briefcase must be re-generated by running ``briefcase create android gradle``. If customizations were made to files within the generated app, they will need to be manually re-applied after re-running the create command. (`#1065 <https://github.com/beeware/briefcase/issues/1065>`__)
* Flatpak apps no longer default to using the Freedesktop runtime and SDK version 21.08 when a runtime is not specified. Instead, the runtime now must be explicitly defined in the `application configuration <https://briefcase.readthedocs.io/en/latest/reference/platforms/linux/flatpak.html#application-configuration>`__. (`#1272 <https://github.com/beeware/briefcase/pull/1272>`__)


Documentation
-------------

* All code blocks were updated to add a button to copy the relevant contents on to the user's clipboard. (`#1213 <https://github.com/beeware/briefcase/pull/1213>`__)
* The limitations of using WebKit2 in AppImage were documented. (`#1322 <https://github.com/beeware/briefcase/issues/1322>`__)

Misc
----

* `#856 <https://github.com/beeware/briefcase/issues/856>`__, `#1093 <https://github.com/beeware/briefcase/pull/1093>`__, `#1178 <https://github.com/beeware/briefcase/pull/1178>`__, `#1181 <https://github.com/beeware/briefcase/pull/1181>`__, `#1186 <https://github.com/beeware/briefcase/pull/1186>`__, `#1187 <https://github.com/beeware/briefcase/issues/1187>`__, `#1191 <https://github.com/beeware/briefcase/pull/1191>`__, `#1192 <https://github.com/beeware/briefcase/pull/1192>`__, `#1193 <https://github.com/beeware/briefcase/pull/1193>`__, `#1195 <https://github.com/beeware/briefcase/issues/1195>`__, `#1197 <https://github.com/beeware/briefcase/pull/1197>`__, `#1200 <https://github.com/beeware/briefcase/pull/1200>`__, `#1204 <https://github.com/beeware/briefcase/pull/1204>`__, `#1205 <https://github.com/beeware/briefcase/pull/1205>`__, `#1206 <https://github.com/beeware/briefcase/pull/1206>`__, `#1215 <https://github.com/beeware/briefcase/pull/1215>`__, `#1226 <https://github.com/beeware/briefcase/pull/1226>`__, `#1228 <https://github.com/beeware/briefcase/pull/1228>`__, `#1232 <https://github.com/beeware/briefcase/pull/1232>`__, `#1233 <https://github.com/beeware/briefcase/pull/1233>`__, `#1239 <https://github.com/beeware/briefcase/pull/1239>`__, `#1241 <https://github.com/beeware/briefcase/pull/1241>`__, `#1242 <https://github.com/beeware/briefcase/pull/1242>`__, `#1243 <https://github.com/beeware/briefcase/pull/1243>`__, `#1244 <https://github.com/beeware/briefcase/pull/1244>`__, `#1246 <https://github.com/beeware/briefcase/pull/1246>`__, `#1248 <https://github.com/beeware/briefcase/pull/1248>`__, `#1249 <https://github.com/beeware/briefcase/issues/1249>`__, `#1253 <https://github.com/beeware/briefcase/pull/1253>`__, `#1254 <https://github.com/beeware/briefcase/pull/1254>`__, `#1255 <https://github.com/beeware/briefcase/pull/1255>`__, `#1257 <https://github.com/beeware/briefcase/pull/1257>`__, `#1258 <https://github.com/beeware/briefcase/pull/1258>`__, `#1262 <https://github.com/beeware/briefcase/pull/1262>`__, `#1263 <https://github.com/beeware/briefcase/pull/1263>`__, `#1264 <https://github.com/beeware/briefcase/pull/1264>`__, `#1265 <https://github.com/beeware/briefcase/pull/1265>`__, `#1273 <https://github.com/beeware/briefcase/pull/1273>`__, `#1274 <https://github.com/beeware/briefcase/pull/1274>`__, `#1279 <https://github.com/beeware/briefcase/pull/1279>`__, `#1282 <https://github.com/beeware/briefcase/pull/1282>`__, `#1283 <https://github.com/beeware/briefcase/pull/1283>`__, `#1284 <https://github.com/beeware/briefcase/pull/1284>`__, `#1293 <https://github.com/beeware/briefcase/pull/1293>`__, `#1294 <https://github.com/beeware/briefcase/pull/1294>`__, `#1295 <https://github.com/beeware/briefcase/pull/1295>`__, `#1299 <https://github.com/beeware/briefcase/pull/1299>`__, `#1300 <https://github.com/beeware/briefcase/pull/1300>`__, `#1301 <https://github.com/beeware/briefcase/pull/1301>`__, `#1310 <https://github.com/beeware/briefcase/pull/1310>`__, `#1311 <https://github.com/beeware/briefcase/pull/1311>`__, `#1316 <https://github.com/beeware/briefcase/pull/1316>`__, `#1317 <https://github.com/beeware/briefcase/pull/1317>`__, `#1323 <https://github.com/beeware/briefcase/pull/1323>`__, `#1324 <https://github.com/beeware/briefcase/pull/1324>`__, `#1333 <https://github.com/beeware/briefcase/pull/1333>`__, `#1334 <https://github.com/beeware/briefcase/pull/1334>`__, `#1335 <https://github.com/beeware/briefcase/pull/1335>`__, `#1336 <https://github.com/beeware/briefcase/pull/1336>`__, `#1339 <https://github.com/beeware/briefcase/issues/1339>`__, `#1341 <https://github.com/beeware/briefcase/pull/1341>`__, `#1350 <https://github.com/beeware/briefcase/pull/1350>`__, `#1351 <https://github.com/beeware/briefcase/pull/1351>`__


0.3.14 (2023-04-12)
===================

Features
--------

* Added support for code signing Windows apps. (`#366 <https://github.com/beeware/briefcase/issues/366>`__)
* The base image used to build AppImages is now user-configurable. (`#947 <https://github.com/beeware/briefcase/issues/947>`__)
* Support for Arch ``.pkg.tar.zst`` packaging was added to the Linux system backend. (`#1064 <https://github.com/beeware/briefcase/issues/1064>`__)
* Pygame was added as an explicit option for a GUI toolkit. (`#1125 <https://github.com/beeware/briefcase/pull/1125>`__)
* AppImage and Flatpak builds now use `indygreg's Python Standalone Builds <https://github.com/indygreg/python-build-standalone>`__ to provide Python support. (`#1132 <https://github.com/beeware/briefcase/pull/1132>`__)
* BeeWare now has a presence on Mastodon. (`#1142 <https://github.com/beeware/briefcase/pull/1142>`__)


Bugfixes
--------

* When commands produce output that cannot be decoded to Unicode, Briefcase now writes the bytes as hex instead of truncating output or canceling the command altogether. (`#1141 <https://github.com/beeware/briefcase/issues/1141>`__)
* When ``JAVA_HOME`` contains a path to a file instead of a directory, Briefcase will now warn the user and install an isolated copy of Java instead of logging a ``NotADirectoryError``. (`#1144 <https://github.com/beeware/briefcase/pull/1144>`__)
* If the Docker ``buildx`` plugin is not installed, users are now directed by Briefcase to install it instead of Docker failing to build the image. (`#1153 <https://github.com/beeware/briefcase/pull/1153>`__)


Misc
----

* `#1133 <https://github.com/beeware/briefcase/pull/1133>`__, `#1138 <https://github.com/beeware/briefcase/pull/1138>`__, `#1139 <https://github.com/beeware/briefcase/pull/1139>`__, `#1140 <https://github.com/beeware/briefcase/pull/1140>`__, `#1147 <https://github.com/beeware/briefcase/pull/1147>`__, `#1148 <https://github.com/beeware/briefcase/pull/1148>`__, `#1149 <https://github.com/beeware/briefcase/pull/1149>`__, `#1150 <https://github.com/beeware/briefcase/pull/1150>`__, `#1151 <https://github.com/beeware/briefcase/pull/1151>`__, `#1156 <https://github.com/beeware/briefcase/pull/1156>`__, `#1162 <https://github.com/beeware/briefcase/pull/1162>`__, `#1163 <https://github.com/beeware/briefcase/pull/1163>`__, `#1168 <https://github.com/beeware/briefcase/pull/1168>`__, `#1169 <https://github.com/beeware/briefcase/pull/1169>`__, `#1170 <https://github.com/beeware/briefcase/pull/1170>`__, `#1171 <https://github.com/beeware/briefcase/pull/1171>`__, `#1172 <https://github.com/beeware/briefcase/pull/1172>`__, `#1173 <https://github.com/beeware/briefcase/pull/1173>`__, `#1177 <https://github.com/beeware/briefcase/pull/1177>`__


0.3.13 (2023-03-10)
===================

Features
--------

* Distribution artefacts are now generated into a single ``dist`` folder. (`#424 <https://github.com/beeware/briefcase/issues/424>`__)
* When installing application sources and dependencies, any ``__pycache__`` folders are now automatically removed. (`#986 <https://github.com/beeware/briefcase/issues/986>`__)
* A Linux System backend was added, supporting ``.deb`` as a packaging format. (`#1062 <https://github.com/beeware/briefcase/issues/1062>`__)
* Support for ``.rpm`` packaging was added to the Linux system backend. (`#1063 <https://github.com/beeware/briefcase/issues/1063>`__)
* Support for passthrough arguments was added to the ``dev`` and ``run`` commands. (`#1077 <https://github.com/beeware/briefcase/issues/1077>`__)
* Users can now define custom content to include in their ``pyscript.toml`` configuration file for web deployments. (`#1089 <https://github.com/beeware/briefcase/issues/1089>`__)
* The ``new`` command now allows for specifying a custom template branch, as well as a custom template. (`#1101 <https://github.com/beeware/briefcase/pull/1101>`__)

Bugfixes
--------

* Spaces are no longer used in the paths for generated app templates. (`#804 <https://github.com/beeware/briefcase/issues/804>`__)
* The stub executable used by Windows now clears the threading mode before starting the Python app. This caused problems with displaying dialogs in Qt apps. (`#930 <https://github.com/beeware/briefcase/issues/930>`__)
* Briefcase now prevents running commands targeting Windows platforms when not on Windows. (`#1010 <https://github.com/beeware/briefcase/issues/1010>`__)
* The command to store notarization credentials no longer causes Briefcase to hang. (`#1100 <https://github.com/beeware/briefcase/pull/1100>`__)
* macOS developer tool installation prompts have been improved. (`#1122 <https://github.com/beeware/briefcase/pull/1122>`__)

Misc
----

* `#1070 <https://github.com/beeware/briefcase/pull/1070>`__, `#1074 <https://github.com/beeware/briefcase/pull/1074>`__, `#1075 <https://github.com/beeware/briefcase/pull/1075>`__, `#1076 <https://github.com/beeware/briefcase/pull/1076>`__, `#1080 <https://github.com/beeware/briefcase/pull/1080>`__, `#1084 <https://github.com/beeware/briefcase/pull/1084>`__, `#1085 <https://github.com/beeware/briefcase/pull/1085>`__, `#1086 <https://github.com/beeware/briefcase/pull/1086>`__, `#1087 <https://github.com/beeware/briefcase/issues/1087>`__, `#1094 <https://github.com/beeware/briefcase/pull/1094>`__, `#1096 <https://github.com/beeware/briefcase/pull/1096>`__, `#1097 <https://github.com/beeware/briefcase/pull/1097>`__, `#1098 <https://github.com/beeware/briefcase/pull/1098>`__, `#1103 <https://github.com/beeware/briefcase/pull/1103>`__, `#1109 <https://github.com/beeware/briefcase/pull/1109>`__, `#1110 <https://github.com/beeware/briefcase/pull/1110>`__, `#1111 <https://github.com/beeware/briefcase/pull/1111>`__, `#1119 <https://github.com/beeware/briefcase/pull/1119>`__, `#1120 <https://github.com/beeware/briefcase/pull/1120>`__, `#1130 <https://github.com/beeware/briefcase/pull/1130>`__

0.3.12 (2023-01-30)
===================

Features
--------

* Briefcase is more resilient to file download failures by discarding partially downloaded files. (`#753 <https://github.com/beeware/briefcase/issues/753>`__)
* All warnings from the App and its dependencies are now shown when running ``briefcase dev`` by invoking Python in `development mode <https://docs.python.org/3/library/devmode.html>`_. (`#806 <https://github.com/beeware/briefcase/issues/806>`__)
* The Dockerfile used to build AppImages can now include user-provided container setup instructions. (`#886 <https://github.com/beeware/briefcase/issues/886>`__)
* It is no longer necessary to specify a device when building an iOS project. (`#953 <https://github.com/beeware/briefcase/pull/953>`__)
* Briefcase apps can now provide a test suite. ``briefcase run`` and ``briefcase dev`` both provide a ``--test`` option to start the test suite. (`#962 <https://github.com/beeware/briefcase/pull/962>`__)
* Initial support for Python 3.12 was added. (`#965 <https://github.com/beeware/briefcase/pull/965>`__)
* Frameworks contained added to a macOS app bundle are now automatically code signed. (`#971 <https://github.com/beeware/briefcase/pull/971>`__)
* The ``build.gradle`` file used to build Android apps can now include arbitrary additional settings. (`#973 <https://github.com/beeware/briefcase/issues/973>`__)
* The run and build commands now have full control over the update of app requirements resources. (`#983 <https://github.com/beeware/briefcase/pull/983>`__)
* Resources that require variants will now use the variant name as part of the filename by default. (`#989 <https://github.com/beeware/briefcase/pull/989>`__)
* ``briefcase open linux appimage`` now starts a shell session in the Docker context, rather than opening the project folder. (`#991 <https://github.com/beeware/briefcase/issues/991>`__)
* Web project configuration has been updated to reflect recent changes to PyScript. (`#1004 <https://github.com/beeware/briefcase/issues/1004>`__)

Bugfixes
--------

* Console output of Windows apps is now captured in the Briefcase log. (`#787 <https://github.com/beeware/briefcase/issues/787>`__)
* Android emulators configured with ``_no_skin`` will no longer generate a warning. (`#882 <https://github.com/beeware/briefcase/issues/882>`__)
* Briefcase now exits normally when CTRL-C is sent while tailing logs for the App when using ``briefcase run``. (`#904 <https://github.com/beeware/briefcase/issues/904>`__)
* Backslashes and double quotes are now safe to be used for formal name and description (`#905 <https://github.com/beeware/briefcase/issues/905>`__)
* The console output for Windows batch scripts in now captured in the Briefcase log. (`#917 <https://github.com/beeware/briefcase/issues/917>`__)
* When using the Windows Store version of Python, Briefcase now ensures the cache directory is created in ``%LOCALAPPDATA%`` instead of the sandboxed location enforced for Windows Store apps. (`#922 <https://github.com/beeware/briefcase/issues/922>`__)
* An Android application that successfully starts, but fails quickly, no longer stalls the launch process. (`#936 <https://github.com/beeware/briefcase/issues/936>`__)
* The required Visual Studio Code components are now included in verification errors for Visual Studio Apps. (`#939 <https://github.com/beeware/briefcase/issues/939>`__)
* It is now possible to specify app configurations for macOS Xcode and Windows VisualStudio projects. Previously, these sections of configuration files would be ignored due to a case discrepancy. (`#952 <https://github.com/beeware/briefcase/pull/952>`__)
* Development mode now starts apps in PEP540 UTF-8 mode, for consistency with the stub apps. (`#985 <https://github.com/beeware/briefcase/pull/985>`__)
* Local file references in requirements no longer break AppImage builds. (`#992 <https://github.com/beeware/briefcase/issues/992>`__)
* On macOS, Rosetta is now installed automatically if needed. (`#1000 <https://github.com/beeware/briefcase/issues/1000>`__)
* The way dependency versions are specified has been modified to make Briefcase as accommodating as possible with end-user environments, but as stable as possible for development environments. (`#1041 <https://github.com/beeware/briefcase/pull/1041>`__)
* To prevent console corruption, dynamic console elements (such as the Wait Bar) are temporarily removed when output streaming is disabled for a command. (`#1055 <https://github.com/beeware/briefcase/issues/1055>`__)


Improved Documentation
----------------------

* Release history now contains links to GitHub issues. (`#1022 <https://github.com/beeware/briefcase/pull/1022>`__)


Misc
----

* #906, #907, #918, #923, #924, #925, #926, #929, #931, #951, #959, #960, #964,
  #967, #969, #972, #981, #984, #987, #994, #995, #996, #997, #1001, #1002,
  #1003, #1012, #1013, #1020, #1021, #1023, #1028, #1038, #1042, #1043, #1044,
  #1045, #1046, #1047, #1048, #1049, #1051, #1052, #1057, #1059, #1061, #1068,
  #1069, #1071


0.3.11 (2022-10-14)
===================

Features
--------

* Added support for deploying an app as a static web page using PyScript. (#3)
* Briefcase log files are now stored in the ``logs`` subdirectory and only when the current directory is a Briefcase project. (#883)

Bugfixes
--------

* Output from spawned Python processes, such as when running ``briefcase dev``, is no longer buffered and displays in the console immediately. (#891)

Misc
----

* #848, #885, #887, #888, #889, #893, #894, #895, #896, #897, #899, #900, #908, #909, #910, #915


0.3.10 (2022-09-28)
===================

Features
--------

* iOS and Android now supports the installation of binary packages. (#471)
* Apps can now selectively remove files from the final app bundle using the ``cleanup_paths`` attribute. (#550)
* The Docker image for AppImage builds is created or updated for all commands instead of just ``create``. (#796)
* The performance of Briefcase's tool verification process has been improved. (#801)
* Briefcase templates are now versioned by the Briefcase version, rather than the Python version. (#824)
* Android commands now start faster, as they only gather a list of SDK packages when needed to write a log file. (#832)
* Log messages can be captured on iOS if they originate from a dynamically loaded module. (#842)
* Added an "open" command that can be used to open projects in IDEs. (#846)

Bugfixes
--------

* The Wait Bar is disabled for batch scripts on Windows to prevent hiding user prompts when CTRL+C is pressed. (#811)
* Android emulators that don't provide a model identifier can now be used to launch apps. (#820)
* All ``linuxdeploy`` plugins are made executable and ELF headers for AppImage plugins are patched for use in ``Docker``. (#829)
* The RCEdit plugin can now be upgraded. (#837)
* When verifying the existence of the Android emulator, Briefcase now looks for the actual binary, not the folder
  that contains the binary. This was causing false positives on some Android SDK setups. (#841)
* When CTRL+C is entered while an external program is running, ``briefcase`` will properly abort and exit. (#851)
* An issue with running `briefcase dev` on projects that put their application module in the project root has been resolved. (#863)

Improved Documentation
----------------------

* Added FAQ entries on the state of binary package support on mobile. (#471)

Misc
----

* #831, #834, #840, #844, #857, #859, #867, #868, #874, #878, #879


0.3.9 (2022-08-17)
==================

Features
--------

* Linux apps can now be packaged in Flatpak format. (#359)
* SDKs, tools, and other downloads needed to support app builds are now stored in an OS-native user cache directory instead of ``~/.briefcase``. (#374)
* Windows MSI installers can now be configured to ask the user whether they want a per-user or per-machine install. (#382)
* The console output of Windows apps is now captured and displayed during ``briefcase run``. (#620)
* Windows apps are now packaged with a stub application. This ensures that Windows apps present with the name and icon of the app, rather than the ``pythonw.exe`` name and icon. It also allows for improvements in logging and error handling. (#629)
* Temporary docker containers are now cleaned up after use. The wording of Docker progress messages has also been improved. (#774)
* Users can now define a ``BRIEFCASE_HOME`` environment variable. This allows you to specify the location of the Briefcase tool cache, allowing the user to avoid issues with spaces in paths or disk space limitations. (#789)
* Android emulator output is now printed to the console if it fails to start properly. (#799)
* ``briefcase android run`` now shows logs from only the current process, and includes all log tags except some particularly noisy and useless ones. It also no longer clears the ``logcat`` buffer. (#814)


Bugfixes
--------

* Apps now have better isolation against the current working directory. This ensures that code in the current working directory isn't inadvertently included when an app runs. (#662)
* Windows MSI installers now install in ``Program Files``, rather than ``Program Files (x86)``. (#688)
* Linuxdeploy plugins can now be used when building Linux AppImages; this resolves many issues with GTK app deployment. (#756)
* Collision protection has been added to custom support packages that have the same name, but are served by different URLs. (#797)
* Python 3.7 and 3.8 on Windows will no longer deadlock when CTRL+C is sent during a subprocess command. (#809)


Misc
----

* #778, #783, #784, #785, #786, #787, #794, #800, #805, #810, #813, #815


0.3.8 (2022-06-27)
==================

Features
--------

* macOS apps are now notarized as part of the packaging process. (#365)
* Console output now uses Rich to provide visual highlights and progress bars. (#740)
* The macOS log streamer now automatically exits using the run command when the app exits. (#742)
* A verbose log is written to file when a critical error occurs or --log is specified. (#760)

Bugfixes
--------

* Updating an Android app now forces a re-install of the app. This corrects a problem (usually seen on physical devices) where app updates wouldn't be deployed if the app was already on the device. (#395)
* The iOS simulator is now able to correctly detect the iOS version when only a device name is provided. (#528)
* Windows MSI projects are now able to support files with non-ASCII filenames. (#749)
* The existence of an appropriate Android system image is now verified independently to the existence of the emulator. (#762)
* The error message presented when the Xcode Command Line Tools are installed, but Xcode is not, has been clarified. (#763)
* The METADATA file generated by Briefcase is now UTF-8 encoded, so it can handle non-Latin-1 characters. (#767)
* Output from subprocesses is correctly encoded, avoiding errors (especially on Windows) when tool output includes non-ASCII content. (#770)


Improved Documentation
----------------------

* Documented a workaround for ELF load command address/offset errors seen when using manylinux wheels. (#718)

Misc
----

* #743, #744, #755


0.3.7 (2022-05-17)
==================

Features
--------

* Apps can be updated as part of a call to package. (#473)
* The Android emulator can now be used on Apple M1 hardware. (#616)
* Names that are reserved words in Python (or other common programming languages) are now prevented when creating apps. (#617)
* Names that are invalid on Windows as filenames (such as CON and LPT0) are now invalid as app names. (#685)
* Verbose logging via ``-v`` and ``-vv`` now includes the return code, output, and environment variables for shell commands (#704)
* When the output of a wrapped command cannot be parsed, full command output, and failure reason is now logged. (#728)
* The iOS emulator will now run apps natively on M1 hardware, rather than through Rosetta emulation. (#739)


Bugfixes
--------

* Bundle identifiers are now validated to ensure they don't contain reserved words. (#460)
* The error reporting when the user is on an unsupported platform or Python version has been improved. (#541)
* When the formal name uses non-Latin characters, the suggested Class and App names are now valid. (#612)
* The code signing process for macOS apps has been made more robust. (#652)
* macOS app binaries are now adhoc signed by default, ensuring they can run on M1 hardware. (#664)
* Xcode version checks are now more robust. (#668)
* Android projects that have punctuation in their formal names can now build without error. (#696)
* Bundle name validation no longer excludes valid country identifiers (like ``in.example``). (#709)
* Application code and dist-info is now fully replaced during an update. (#720)
* Errors related to Java JDK detection now properly contain the value of JAVA_HOME instead of the word None (#727)
* All log entries will now be displayed for the run command on iOS and macOS; previously, initial log entries may have been omitted. (#731)
* Using CTRL+C to stop showing Android emulator logs while running the app will no longer cause the emulator to shutdown. (#733)


Misc
----

* #680, #681, #699, #726, #734


0.3.6 (2022-02-28)
==================

Features
--------

* On macOS, iOS, and Android, ``briefcase run`` now displays the application logs once the application has started. (#591)
* Xcode detection code now allows for Xcode to be installed in locations other than ``/Applications/Xcode.app``. (#622)
* Deprecated support for Python 3.6. (#653)


Bugfixes
--------

* Existing app packages are now cleared before reinstalling dependencies. (#644)
* Added binary patch tool for AppImages to increase compatibility. (#667)


Improved Documentation
----------------------

* Documentation on creating macOS/iOS code signing identities has been added (#641)


Misc
----

* #587, #588, #592, #598, #621, #643, #654, #670


0.3.5 (2021-03-06)
==================

Features
--------

* macOS projects can now be generated as an Xcode project. (#523)

Bugfixes
--------

* macOS apps are now built as an embedded native binary, rather than a shell script invoking a Python script. This was necessary to provide better support for macOS app notarization and sandboxing. (#523)
* Fixed the registration of setuptools entry points caused by a change in case sensitivity handling in Setuptools 53.1.0. (#574)

Misc
----

* #562


0.3.4 (2021-01-03)
==================

Features
--------

* Added signing options for all platforms. App signing is only implemented on macOS, but ``--no-sign`` can now be used regardless of your target platform. (#486)
* Windows MSI installers can be configured to be per-machine, system-wide installers. (#498)
* Projects can specify a custom branch for the template used to generate the app. (#519)
* Added the `--no-run` flag to the *dev* command. This allows developers to install app dependencies without running the app. (#522)
* The new project wizard will now warn users when they select a platform that doesn't support mobile deployment. (#539)

Bugfixes
--------

* Modified the volume mounting process to allow for SELinux. (#500)
* Fixed missing signature for Python executable in macOS app bundle. This enables the packaged dmg to be notarized by Apple. (#514)
* Modified the Windows tests to allow them to pass on 32-bit machines. (#521)
* Fixed a crash when running with verbose output. (#532)

Improved Documentation
----------------------

* Clarified documentation around system_requires dependencies on Linux. (#459)

Misc
----

* #465, #475, #496, #512, #518


0.3.3 (2020-07-18)
==================

Features
--------

* WiX is now auto-downloaded when the MSI backend is used. (#389)
* The ``upgrade`` command now provides a way to upgrade tools that Briefcase has
  downloaded, including WiX, Java, Linuxdeploy, and the Android SDK. (#450)

Bugfixes
--------

* Binary modules in Linux AppImages are now processed correctly, ensuring that no references to system libraries are retained in the AppImage. (#420)
* If pip is configured to use a per-user site_packages, this no longer clashes with the installation of application packages. (#441)
* Docker-using commands now check whether the Docker daemon is running and if the user has permission to access it. (#442)


0.3.2 (2020-07-04)
==================

Features
--------

* Added pytest coverage to CI/CD process. (#417)
* Application metadata now contains a ``Briefcase-Version`` indicator. (#425)
* The device list returned by ``briefcase run android`` now uses the Android device model name and unique ID e.g. a Pixel 3a shows up as ``Pixel 3a (adbDeviceId)``. (#433)
* Android apps are now packaged in Android App Bundle format. This allows the Play Store to dynamically build the smallest APK appropriate to a device installing an app. (#438)
* PursuedPyBear is now included in the new project wizard. (#440)

Bugfixes
--------

* iOS builds will now warn if the Xcode command line tools are the active. (#397)
* Linux Docker builds no longer use interactive mode, allowing builds to run on CI (or other TTY-less devices). (#439)

Improved Documentation
----------------------

* Documented the process of signing Android apps & publishing them to the Google Play store. (#342)

Misc
----

* #428


0.3.1 (2020-06-13)
==================

Features
--------

* The Linux AppImage backend has been modified to use Docker. This ensures that the AppImage is always built in an environment that is compatible with the support package. It also enables Linux AppImages to be built on macOS and Windows. "Native" builds (i.e., builds that *don't* use Docker) can be invoked using the ``--no-docker`` argument. (#344)
* A ``PYTHONPATH`` property has been added to ``AppConfig`` that describes the ``sys.path`` changes needed to run the app. (#401)
* Ad-hoc code signing is now possible on macOS with ``briefcase package --adhoc-sign``. (#409)
* Android apps can now use use ``-`` in their bundle name; we now convert ``-`` to ``_`` in the resulting Android package identifier and Java package name. (#415)
* Mobile applications now support setting the background color of the splash screen, and setting a build identifier. (#422)
* Android now has a ``package`` command that produces the release APK. After manually signing this APK, it can be published to the Google Play Store. (#423)

Bugfixes
--------

* Some stray punctuation in the Android device helper output has been removed. (#396)
* An explicit version check for Docker is now performed. (#402)
* The Linux build process ensures the Docker user matches the UID/GID of the host user. (#403)
* Briefcase now ensures that the Python installation ecosystem tools (``pip``, ``setuptools``, and ``wheel``), are all present and up to date. (#421)

Improved Documentation
----------------------

* Documented that Windows MSI builds produce per-user installable MSI installers, while still supporting per-machine installs via the CLI. (#382)
* ``CONTRIBUTING.md`` has been updated to link to Briefcase-specific documentation. (#404)
* Removed references to the ``build-system`` table in ``pyproject.toml``. (#410)

Misc
----

* #380, #384


0.3.0 (2020-04-18)
==================
Features
--------

* Converted Briefcase to be a PEP518 tool, rather than a setuptools extension. (#266)


0.2.10
======

* Improved pre-detection of Xcode and related tools
* Improved error handling when starting external tools
* Fixed iOS simulator integration

0.2.9
=====

* Updated mechanism for starting the iOS simulator
* Added support for environment markers in ``install_requires``
* Improved error handling when WiX isn't found

0.2.8
=====

* Corrects packaging problem with ``urllib3``, caused by inconsistency between
  ``requests`` and ``boto3``.
* Corrected problems with Start menu targets being created on Windows.

0.2.7
=====

* Added support for launch images for iPhone X, Xs, Xr, Xs Max and Xr Max
* Completed removal of internal pip API dependencies.

0.2.6
=====

* Added support for registering OS-level document type handlers.
* Removed dependency on an internal pip API.
* Corrected invocation of gradlew on Windows
* Addressed support for support builds greater than b9.

0.2.5
=====

* Restored download progress bars when downloading support packages.

0.2.4
=====

* Corrected a bug in the iOS backend that prevented iOS builds.

0.2.3
=====

* Bugfix release, correcting the fix for pip 10 support.

0.2.2
=====

* Added compatibility with pip 10.
* Improved Windows packaging to allow for multiple executables
* Added a ``--clean`` command line option to force a refresh of generated code.
* Improved error handling for bad builds

0.2.1
=====

* Improved error reporting when a support package isn't available.

0.2.0
=====

* Added ``-s`` option to launch projects
* Switch to using AWS S3 resources rather than GitHub Files.

0.1.9
=====

* Added a full Windows installer backend

0.1.8
=====

* Modified template roll out process to avoid API limits on GitHub.

0.1.7
=====

* Added check for existing directories, with the option to replace existing content.
* Added a Linux backend.
* Added a Windows backend.
* Added a splash screen for Android

0.1.6
=====

* Added a Django backend (``@glasnt``)

0.1.5
=====

* Added initial Android template
* Force versions of pip (>= 8.1) and setuptools (>=27.0)
* Drop support for Python 2

0.1.4
=====

* Added support for tvOS projects
* Moved to using branches in the project template repositories.

0.1.3
=====

* Added support for Android projects using VOC.

0.1.2
=====

* Added support for having multi-target support projects. This clears the way for Briefcase to be used for watchOS and tvOS projects, and potentially for Python-OSX-support and Python-iOS-support to be merged into a single Python-Apple-support.

0.1.1
=====

* Added support for app icons and splash screens.

0.1.0
=====

* Initial public release.
