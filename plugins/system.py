from config import ADMIN_ID
import psutil
import shutil

def setup(bot):

    @bot.message_handler(commands=['system', 'sysinfo'])
    def system_info(message):
        if message.from_user.id != ADMIN_ID:
            return
            
        try:
            # RAM ഉപയോഗം പരിശോധിക്കുന്നു
            ram = psutil.virtual_memory()
            ram_total = round(ram.total / (1024**3), 2)
            ram_used = round(ram.used / (1024**3), 2)
            ram_percent = ram.percent
            
            # ഡിസ്ക് (Hard Disk) ഉപയോഗം പരിശോധിക്കുന്നു
            disk = shutil.disk_usage("/")
            disk_total = round(disk.total / (1024**3), 2)
            disk_used = round(disk.used / (1024**3), 2)
            disk_percent = round((disk.used / disk.total) * 100, 2)
            
            # CPU ഉപയോഗം പരിശോധിക്കുന്നു
            cpu_percent = psutil.cpu_percent(interval=1)
            
            sys_text = (
                f"🖥️ **Server System Status:**\n\n"
                f"🧠 **RAM Usage:** `{ram_used}GB / {ram_total}GB` (`{ram_percent}%`)\n"
                f"💾 **Disk Space:** `{disk_used}GB / {disk_total}GB` (`{disk_percent}%`)\n"
                f"⚡ **CPU Usage:** `{cpu_percent}%`\n\n"
                f"🟢 **Status:** `Running Smoothly`"
            )
            
            bot.reply_to(message, sys_text, parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Error fetching system info: `{e}`", parse_mode='Markdown')
