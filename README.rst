import tkinter as tk
from tkinter import filedialog, messagebox
from cryptography.fernet import Fernet
import os

class SecureCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("ماشین حساب امن با قفل فایل")
        self.root.geometry("400x600")
        
        # ایجاد کلید رمزنگاری اگر وجود نداشته باشد
        self.key_file = "secret.key"
        if not os.path.exists(self.key_file):
            self.generate_key()
        
        # بارگذاری کلید
        with open(self.key_file, "rb") as key_file:
            self.key = key_file.read()
        self.cipher_suite = Fernet(self.key)
        
        # متغیرهای ماشین حساب
        self.current_input = ""
        self.result_var = tk.StringVar()
        
        # ایجاد رابط کاربری
        self.create_calculator_ui()
        self.create_file_lock_ui()
    
    def generate_key(self):
        """تولید کلید رمزنگاری و ذخیره در فایل"""
        key = Fernet.generate_key()
        with open(self.key_file, "wb") as key_file:
            key_file.write(key)
    
    def create_calculator_ui(self):
        """ایجاد بخش ماشین حساب"""
        calculator_frame = tk.LabelFrame(self.root, text="ماشین حساب", padx=10, pady=10)
        calculator_frame.pack(pady=10, fill="both", expand="yes")
        
        # نمایشگر نتیجه
        display = tk.Entry(calculator_frame, textvariable=self.result_var, font=('Arial', 18), bd=10, insertwidth=2,
                         width=14, borderwidth=4, justify="right")
        display.grid(row=0, column=0, columnspan=4)
        
        # دکمه‌های ماشین حساب
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+',
            'C'
        ]
        
        row = 1
        col = 0
        for button in buttons:
            if button == 'C':
                tk.Button(calculator_frame, text=button, padx=20, pady=20, font=('Arial', 14),
                          command=self.clear_all).grid(row=row, column=col, columnspan=4, sticky="nsew")
            else:
                tk.Button(calculator_frame, text=button, padx=20, pady=20, font=('Arial', 14),
                          command=lambda b=button: self.on_button_click(b)).grid(row=row, column=col, sticky="nsew")
            
            col += 1
            if col > 3:
                col = 0
                row += 1
    
    def create_file_lock_ui(self):
        """ایجاد بخش قفل فایل"""
        file_frame = tk.LabelFrame(self.root, text="قفل فایل‌های چندرسانه‌ای", padx=10, pady=10)
        file_frame.pack(pady=10, fill="both", expand="yes")
        
        tk.Button(file_frame, text="انتخاب فایل برای قفل کردن", command=self.lock_file, 
                 font=('Arial', 12), padx=10, pady=5).pack(fill="x")
        tk.Button(file_frame, text="انتخاب فایل برای باز کردن قفل", command=self.unlock_file, 
                 font=('Arial', 12), padx=10, pady=5).pack(fill="x")
    
    def on_button_click(self, char):
        """مدیریت کلیک دکمه‌های ماشین حساب"""
        if char == '=':
            try:
                self.current_input = str(eval(self.current_input))
                self.result_var.set(self.current_input)
            except:
                self.result_var.set("خطا")
                self.current_input = ""
        else:
            self.current_input += str(char)
            self.result_var.set(self.current_input)
    
    def clear_all(self):
        """پاک کردن همه چیز"""
        self.current_input = ""
        self.result_var.set("")
    
    def lock_file(self):
        """قفل کردن فایل انتخاب شده"""
        file_path = filedialog.askopenfilename(
            title="فایل را برای قفل کردن انتخاب کنید",
            filetypes=[("فایل‌های چندرسانه‌ای", "*.mp4 *.avi *.mov *.jpg *.jpeg *.png"), ("همه فایل‌ها", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.cipher_suite.encrypt(file_data)
            
            # ذخیره فایل رمز شده
            locked_file_path = file_path + ".locked"
            with open(locked_file_path, 'wb') as file:
                file.write(encrypted_data)
            
            # حذف فایل اصلی
            os.remove(file_path)
            
            messagebox.showinfo("موفق", f"فایل با موفقیت قفل شد و در آدرس زیر ذخیره شد:\n{locked_file_path}")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در قفل کردن فایل:\n{str(e)}")
    
    def unlock_file(self):
        """باز کردن قفل فایل انتخاب شده"""
        file_path = filedialog.askopenfilename(
            title="فایل قفل شده را برای باز کردن انتخاب کنید",
            filetypes=[("فایل‌های قفل شده", "*.locked"), ("همه فایل‌ها", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'rb') as file:
                encrypted_data = file.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # ایجاد نام فایل اصلی (حذف پسوند .locked)
            original_file_path = file_path.replace(".locked", "")
            
            # ذخیره فایل رمزگشایی شده
            with open(original_file_path, 'wb') as file:
                file.write(decrypted_data)
            
            # حذف فایل قفل شده
            os.remove(file_path)
            
            messagebox.showinfo("موفق", f"فایل با موفقیت باز شد و در آدرس زیر ذخیره شد:\n{original_file_path}")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در باز کردن قفل فایل:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureCalculator(root)
    root.mainloop()
