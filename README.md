import platform
import subprocess
import tkinter as tk
from tkinter import messagebox


def check_device():
  # محاكاة فحص المواصفات (يمكن ربطها بقاعدة بيانات للهواتف لاحقاً)
  phone_name = entry_phone.get()

  if not phone_name:
    messagebox.showerror("خطأ", "الرجاء إدخال اسم أو معالج الهاتف!")
    return

  # قاعدة بيانات بسيطة كمثال لفحص الدعم
  supported_gpus = ["snapdragon 8", "dimensity 9", "apple a16", "apple a17"]

  # نتيجة وهمية للفحص (تطويرها لاحقاً لتعمل على الأندرويد الفعلي)
  result_text.config(
      text=(
          f"الجهاز: {phone_name}\nالحالة: يدعم تشغيل بيس 2027 بكفاءة عالية! 🎮🔥"
      ),
      fg="#00ffff",
  )


# إعداد النافذة الرئيسية
root = tk.Tk()
root.title("كلاوس لايفر جيمز - فاحص أجهزة بيس 2027")
root.geometry("450x550")
root.config(bg="#0f0f1a")

# العنوان الرئيسي
title_label = tk.Label(
    root,
    text="GAMING - PES 2027",
    font=("Arial", 18, "bold"),
    bg="#0f0f1a",
    fg="#ff4757",
)
title_label.pack(pady=20)

# صورة شعار أو وصف فرعي
sub_label = tk.Label(
    root,
    text="افحص هاتفك واعرف إذا كان يدعم اللعبة",
    font=("Arial", 12),
    bg="#0f0f1a",
    fg="#ffffff",
)
sub_label.pack(pady=5)

# حقل إدخال اسم الهاتف
entry_phone = tk.Entry(
    root,
    font=("Arial", 14),
    bg="#1e1e2f",
    fg="#ffffff",
    insertbackground="white",
    justify="center",
)
entry_phone.pack(pady=20, ipadx=10, ipady=5)
entry_phone.insert(0, "أدخل اسم هاتفك هنا...")

# زر الفحص بتصميم يحاكي ألوان قناتك
btn_check = tk.Button(
    root,
    text="فحص الهاتف الآن",
    font=("Arial", 14, "bold"),
    bg="#ff4757",
    fg="#ffffff",
    activebackground="#ff6b81",
    activeforeground="#ffffff",
    relief="flat",
    command=check_device,
)
btn_check.pack(pady=15, ipadx=20, ipady=5)

# مساحة عرض النتيجة
result_text = tk.Label(
    root,
    text="",
    font=("Arial", 12, "bold"),
    bg="#0f0f1a",
    fg="#00ffff",
    justify="center",
)
result_text.pack(pady=30)

# تشغيل التطبيق
root.mainloop()
[<img src="https://beeware.org/project/briefcase/briefcase.png" width="72" alt="logo" />](https://beeware.org/briefcase)

# Briefcase

[![Python Versions](https://img.shields.io/pypi/pyversions/briefcase.svg)](https://pypi.python.org/pypi/briefcase)
[![PyPI Version](https://img.shields.io/pypi/v/briefcase.svg)](https://pypi.python.org/pypi/briefcase)
[![Maturity](https://img.shields.io/pypi/status/briefcase.svg)](https://pypi.python.org/pypi/briefcase)
[![BSD License](https://img.shields.io/pypi/l/briefcase.svg)](https://github.com/beeware/briefcase/blob/main/LICENSE)
[![Build Status](https://github.com/beeware/briefcase/workflows/CI/badge.svg?branch=main)](https://github.com/beeware/briefcase/actions)
[![Discord server](https://img.shields.io/discord/836455665257021440?label=Discord%20Chat&logo=discord&style=plastic)](https://beeware.org/bee/chat/)

Briefcase is a tool for converting a Python project into a standalone native application. You can package projects for:

- Mac
- Windows
- Linux
- iPhone/iPad
- Android
- Web

Support for AppleTV, watchOS, and wearOS deployments is planned.

## Getting started

To install Briefcase, run:

    $ python -m pip install briefcase

If you would like a full introduction to using Briefcase, try the [BeeWare tutorial](https://tutorial.beeware.org). This tutorial walks you through the process of creating and packaging a new application with Briefcase.

## Financial support

The BeeWare project would not be possible without the generous support of our financial members:

[![Anaconda logo](https://beeware.org/images/anaconda-dark.png)](https://anaconda.com/)

Anaconda Inc. - Advancing AI through open source.

Plus individual contributions from [users like you](https://beeware.org/community/members/). If you find Briefcase, or other BeeWare tools useful, please consider becoming a financial member.

## Documentation

Documentation for Briefcase can be found on [Read The Docs](https://briefcase.beeware.org).

## Community

Briefcase is part of the [BeeWare suite](https://beeware.org). You can talk to the community through:

- [@beeware@fosstodon.org on Mastodon](https://fosstodon.org/@beeware)
- [Discord](https://beeware.org/bee/chat/)
- The Briefcase [GitHub Discussions forum](https://github.com/beeware/briefcase/discussions)

We foster a welcoming and respectful community as described in our [BeeWare Community Code of Conduct](https://beeware.org/community/code-of-conduct/).

## Contributing

If you experience problems with Briefcase, [log them on GitHub](https://briefcase.beeware.org/en/latest/how-to/contribute/how/new-issue/).

If you'd like to contribute to Briefcase development, our [contribution guide](https://briefcase.beeware.org/en/latest/how-to/contribute) details how to set up a development environment, and other requirements we have as part of our contribution process.
