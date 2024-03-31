"""Implements the Rubicon API using Chaquopy"""

from java import cast, chaquopy, dynamic_proxy, jarray, jclass


# --- Globals -----------------------------------------------------------------

from java import jboolean, jbyte, jshort, jint, jlong, jfloat, jdouble, jchar, jvoid
jstring = jclass("java.lang.String")

JavaClass = jclass

# This wouldn't work if a class implements multiple interfaces, but Rubicon
# doesn't support that anyway.
def JavaInterface(name):
    return dynamic_proxy(jclass(name))

def JavaNull(cls):
    return cast(_java_class(cls), None)


# --- Class attributes --------------------------------------------------------

@property
def __null__(cls):
    return cast(_java_class(cls), None)
chaquopy.JavaClass.__null__ = __null__

def __cast__(cls, obj, globalref=False):
    return cast(_java_class(cls), obj)
chaquopy.JavaClass.__cast__ = __cast__

# This isn't part of Rubicon's public API, but Toga uses it to work around
# limitations in Rubicon's discovery of which interfaces a class implements.
@property
def _alternates(cls):
    return []
chaquopy.JavaClass._alternates = _alternates

# For Rubicon unit tests.
@property
def _signature(self):
    return self.sig.encode("UTF-8")
chaquopy.NoneCast._signature = _signature


# --- Instance attributes -----------------------------------------------------

Object = jclass("java.lang.Object")

# In Chaquopy, all Java objects exposed to Python code already have global JNI
# references.
def __global__(self):
    return self
Object.__global__ = __global__


# -----------------------------------------------------------------------------

def _java_class(cls):
    if isinstance(cls, list):
        if len(cls) != 1:
            raise ValueError("Expressions for an array class must contain a single item")
        return jarray(_java_class(cls[0]))
    if isinstance(cls, bytes):
        cls = cls.decode("UTF-8")
    if isinstance(cls, str):
        cls = jclass(cls)
    if isinstance(cls, Object):
        # This isn't documented, but it's covered by the Rubicon unit tests.
        cls = type(cls)
    if not isinstance(cls, type):
        raise ValueError(f"Cannot convert {cls!r} to a Java class")

    try:
        return {
            bool: jboolean,
            int: jint,
            float: jfloat,
            str: jstring,
            bytes: jarray(jbyte),
        }[cls]
    except KeyError:
        pass
    if isinstance(cls, chaquopy.DynamicProxyClass):
        # Remove the dynamic_proxy wrapper which JavaInterface added above.
        return cls.implements[0]
    return cls
