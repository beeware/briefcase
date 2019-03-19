import os
from ctypes import Structure, sizeof, c_byte, c_ushort, c_int
from win32ctypes.pywin32 import win32api


# Structures in ico file
class IconHeader(Structure):
    _fields_ = [
        ("Width", c_byte),
        ("Height", c_byte),
        ("Colors", c_byte),
        ("Reserved", c_byte),
        ("Planes", c_ushort),
        ("BitsPerPixel", c_ushort),
        ("ImageSize", c_int),
        ("ImageOffset", c_int),
    ]


class GroupIcon(Structure):
    _fields_ = [
        ("Reserved", c_ushort),
        ("ResourceType", c_ushort),
        ("ImageCount", c_ushort),
        # ("Enries", PIconDirResEntry),
    ]


# Structure for updating resource
class IconDirResEntry(Structure):
    _fields_ = [
        ("Width", c_byte),
        ("Height", c_byte),
        ("Colors", c_byte),
        ("Reserved", c_byte),
        ("Planes", c_ushort),
        ("BitsPerPixel", c_ushort),
        ("ImageSize", c_int),
        ("ResourceID", c_ushort),
    ]


RT_ICON = 3
RT_GROUP_ICON = 14


def apply_icon(icon, dest):
    """
    Use winapi UpdateResource to copy icon into exe

    :param str icon: .ico file path
    :param str dest: path of the .exe to update.
    """

    print("Applying icons from %s to %s", (icon, dest))
    dest = os.path.abspath(dest)

    with open(icon, 'rb') as iconfile:
        # header = GroupIcon()
        group_header_data = iconfile.read(sizeof(GroupIcon))
        group_header = GroupIcon.from_buffer_copy(group_header_data)
        if group_header.ResourceType != 1:
            print("Incorrect icon ResourceType")

        icon_headers = [
            IconHeader.from_buffer_copy(iconfile.read())
        ]

        icon_data = []
        for icon in icon_headers:
            iconfile.seek(icon.ImageOffset)
            icon_data.append(iconfile.read(icon.ImageSize))

    h_exe = win32api.BeginUpdateResource(dest, 0)

    header_data = bytes(group_header)

    for i, header in enumerate(icon_headers):
        res_icon_header = IconDirResEntry()
        for f in ("Width", "Height", "Colors", "Reserved",
                  "Planes", "BitsPerPixel", "ImageSize"):
            setattr(res_icon_header, f, getattr(header, f))
        res_icon_header.ResourceID = i+1
        header_data += bytes(res_icon_header)

    win32api.UpdateResource(h_exe, RT_GROUP_ICON, 0, header_data)

    for i, data in enumerate(icon_data):
        win32api.UpdateResource(h_exe, RT_ICON, i+1, data)

    win32api.EndUpdateResource(h_exe, 0)


if __name__ == '__main__':
    import sys
    apply_icon(sys.argv[1], sys.argv[2])
