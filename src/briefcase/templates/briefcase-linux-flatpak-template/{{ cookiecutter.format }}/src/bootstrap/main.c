//
//  main.c
//  A main module for starting Python projects on Linux.
//
#include <wchar.h>
#include <stdio.h>
#include <Python.h>

int main(int argc, char *argv[]) {
    int ret = 0;
    PyStatus status;
    PyPreConfig preconfig;
    PyConfig config;
    char *python_home;
    char *app_module_name;
    char *path;
    wchar_t *wtmp_str;
    PyObject *app_module;
    PyObject *module;
    PyObject *module_attr;
    PyObject *method_args;
    PyObject *result;
    PyObject *exc_type;
    PyObject *exc_value;
    PyObject *exc_traceback;
    PyObject *systemExit_code;

    // Generate an isolated Python configuration.
    PyPreConfig_InitIsolatedConfig(&preconfig);
    PyConfig_InitIsolatedConfig(&config);

    // Configure the Python interpreter:
    // Enforce UTF-8 encoding for stderr, stdout, file-system encoding and locale.
    // See https://docs.python.org/3/library/os.html#python-utf-8-mode.
    preconfig.utf8_mode = 1;
    // Don't buffer stdio. We want output to appears in the log immediately
    config.buffered_stdio = 0;
    // Don't write bytecode; we can't modify the app bundle
    // after it has been signed.
    config.write_bytecode = 0;
    // Isolated apps need to set the full PYTHONPATH manually.
    config.module_search_paths_set = 1;

    printf("Pre-initializing Python runtime...\n");
    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to pre-initialize Python interpreter: %s", status.err_msg, nil]);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }

    // Set the home for the Python interpreter
    python_home = "/app";
    printf("PYTHONHOME: %s\n", python_home);
    wtmp_str = Py_DecodeLocale(python_home, NULL);
    status = PyConfig_SetString(&config, &config.home, wtmp_str);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set PYTHONHOME: %s", status.err_msg]);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }
    PyMem_RawFree(wtmp_str);

    // Determine the app module name. Look for the BRIEFCASE_MAIN_MODULE
    // environment variable first; if that exists, we're probably in test
    // mode. If it doesn't exist, fall back to the MainModule key in the
    // main bundle.
    app_module_name = getenv("BRIEFCASE_MAIN_MODULE");
    if (app_module_name == NULL) {
        app_module_name = "{{ cookiecutter.module_name }}";
    }
    status = PyConfig_SetBytesString(&config, &config.run_module, app_module_name);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set app module name: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }

    // Read the site config
    status = PyConfig_Read(&config);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to read site config: %s", status.err_msg]);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }

    // Set the full module path. This includes the stdlib, site-packages, and app code.
    printf("PYTHONPATH:\n");
    // // The .zip form of the stdlib
    path = "/app/lib/python{{ ''.join(cookiecutter.python_version.split('.')[:2]) }}.zip";
    printf("- %s\n", path);
    wtmp_str = Py_DecodeLocale(path, NULL);
    status = PyWideStringList_Append(&config.module_search_paths, wtmp_str);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set .zip form of stdlib path: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }
    PyMem_RawFree(wtmp_str);

    // The unpacked form of the stdlib
    path = "/app/lib/python{{ '.'.join(cookiecutter.python_version.split('.')[:2]) }}";
    printf("- %s\n", path);
    wtmp_str = Py_DecodeLocale(path, NULL);
    status = PyWideStringList_Append(&config.module_search_paths, wtmp_str);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set unpacked form of stdlib path: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }
    PyMem_RawFree(wtmp_str);

    // Add the stdlib binary modules path
    path = "/app/lib/python{{ '.'.join(cookiecutter.python_version.split('.')[:2]) }}/lib-dynload";
    printf("- %s\n", path);
    wtmp_str = Py_DecodeLocale(path, NULL);
    status = PyWideStringList_Append(&config.module_search_paths, wtmp_str);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set stdlib binary module path: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }
    PyMem_RawFree(wtmp_str);

    // Add the app_packages path
    path = "/app/briefcase/app_packages";
    printf("- %s\n", path);
    wtmp_str = Py_DecodeLocale(path, NULL);
    status = PyWideStringList_Append(&config.module_search_paths, wtmp_str);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set app path: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }
    PyMem_RawFree(wtmp_str);

    // Add the app path
    path = "/app/briefcase/app";
    printf("- %s\n", path);
    wtmp_str = Py_DecodeLocale(path, NULL);
    status = PyWideStringList_Append(&config.module_search_paths, wtmp_str);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to set app path: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }
    PyMem_RawFree(wtmp_str);

    printf("Configure argc/argv...\n");
    status = PyConfig_SetBytesArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to configured argc/argv: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }

    printf("Initializing Python runtime...\n");
    status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) {
        // crash_dialog("Unable to initialize Python interpreter: %s", status.err_msg);
        PyConfig_Clear(&config);
        Py_ExitStatusException(status);
    }

    // Start the app module.
    //
    // From here to Py_ObjectCall(runmodule...) is effectively
    // a copy of Py_RunMain() (and, more  specifically, the
    // pymain_run_module() method); we need to re-implement it
    // because we need to be able to inspect the error state of
    // the interpreter, not just the return code of the module.
    printf("Running app module: %s\n", app_module_name);
    module = PyImport_ImportModule("runpy");
    if (module == NULL) {
        // crash_dialog(@"Could not import runpy module");
        exit(-2);
    }

    module_attr = PyObject_GetAttrString(module, "_run_module_as_main");
    if (module_attr == NULL) {
        // crash_dialog(@"Could not access runpy._run_module_as_main");
        exit(-3);
    }

    app_module = PyUnicode_FromString(app_module_name);
    if (app_module == NULL) {
        // crash_dialog(@"Could not convert module name to unicode");
        exit(-3);
    }

    method_args = Py_BuildValue("(Oi)", app_module, 0);
    if (method_args == NULL) {
        // crash_dialog(@"Could not create arguments for runpy._run_module_as_main");
        exit(-4);
    }

    // Print a separator to differentiate Python startup logs from app logs,
    // then flush stdout/stderr to ensure all startup logs have been output.
    printf("---------------------------------------------------------------------------\n");
    fflush(stdout);
    fflush(stderr);

    // Invoke the app module
    result = PyObject_Call(module_attr, method_args, NULL);

    if (result == NULL) {
        // Retrieve the current error state of the interpreter.
        PyErr_Fetch(&exc_type, &exc_value, &exc_traceback);
        PyErr_NormalizeException(&exc_type, &exc_value, &exc_traceback);

        if (exc_traceback == NULL) {
            // crash_dialog(@"Could not retrieve traceback");
            exit(-5);
        }

        if (PyErr_GivenExceptionMatches(exc_value, PyExc_SystemExit)) {
            systemExit_code = PyObject_GetAttrString(exc_value, "code");
            if (systemExit_code == NULL) {
                printf("Could not determine exit code\n");
                ret = -10;
            }
            else {
                ret = (int) PyLong_AsLong(systemExit_code);
            }
        } else {
            ret = -6;
        }

        if (ret != 0) {
            printf("Application quit abnormally (Exit code %d)!\n", ret);

            // Restore the error state of the interpreter.
            PyErr_Restore(exc_type, exc_value, exc_traceback);

            // Print exception to stderr.
            // In case of SystemExit, this will call exit()
            PyErr_Print();

            exit(ret);
        }
    }

    Py_Finalize();

    return ret;
}
