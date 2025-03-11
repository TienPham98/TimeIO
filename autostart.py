import sys
import os
import platform
from PyQt6.QtWidgets import QCheckBox, QMessageBox
from PyQt6.QtCore import QSettings


def add_autostart_feature(app_class):
    """
    Thêm tính năng tự động khởi động vào ứng dụng
    """
    # Thêm thuộc tính và phương thức để kiểm tra trạng thái khởi động tự động
    app_class.autostart_enabled = property(lambda self: self.is_autostart_enabled())
    app_class.set_autostart = lambda self, enable: self.setup_autostart(enable)
    app_class.is_autostart_enabled = is_autostart_enabled
    app_class.setup_autostart = setup_autostart

    # Cập nhật phương thức initUI để thêm checkbox autostart
    original_init_ui = app_class.initUI

    def new_init_ui(self):
        original_init_ui(self)

        # Thêm settings autostart vào context menu
        original_show_context_menu = self.showContextMenu

        def new_show_context_menu(pos):
            contextMenu = original_show_context_menu(pos)

            # Thêm action autostart nếu chưa có
            autostartAction = None
            for action in contextMenu.actions():
                if action.text() == "Tự động khởi động cùng Windows":
                    autostartAction = action
                    break

            if not autostartAction:
                contextMenu.insertSeparator(contextMenu.actions()[0])
                autostartAction = QAction("Tự động khởi động cùng Windows", self)
                autostartAction.setCheckable(True)
                autostartAction.setChecked(self.autostart_enabled)
                autostartAction.triggered.connect(lambda checked: self.set_autostart(checked))
                contextMenu.insertAction(contextMenu.actions()[0], autostartAction)

            return contextMenu

        self.showContextMenu = new_show_context_menu

        # Thêm autostart vào dialog cài đặt
        original_open_settings = self.openSettings

        def new_open_settings(self):
            dialog = original_open_settings()

            # Thêm tùy chọn autostart vào dialog cài đặt
            if hasattr(dialog, 'initUI'):
                original_dialog_init_ui = dialog.initUI

                def new_dialog_init_ui(dialog_self):
                    original_dialog_init_ui()

                    # Thêm nhóm cài đặt cho autostart
                    autostartGroup = QGroupBox("Tự động khởi động")
                    autostartLayout = QVBoxLayout()

                    dialog_self.autostartCheckBox = QCheckBox("Tự động khởi động cùng hệ điều hành")
                    dialog_self.autostartCheckBox.setChecked(self.autostart_enabled)
                    autostartLayout.addWidget(dialog_self.autostartCheckBox)

                    autostartGroup.setLayout(autostartLayout)
                    dialog_self.layout().insertWidget(dialog_self.layout().count() - 1, autostartGroup)

                    # Cập nhật phương thức lưu cài đặt
                    original_save_settings = dialog_self.saveSettings

                    def new_save_settings():
                        original_save_settings()
                        self.set_autostart(dialog_self.autostartCheckBox.isChecked())

                    dialog_self.saveSettings = new_save_settings

                dialog.initUI = lambda: new_dialog_init_ui(dialog)

            return dialog

        self.openSettings = new_open_settings

    app_class.initUI = new_init_ui


# Các phương thức theo platform
def is_autostart_enabled(self):
    """Kiểm tra xem ứng dụng có được cài đặt để tự động khởi động không"""
    system = platform.system()

    if system == "Windows":
        import winreg
        app_path = get_app_path()
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
            winreg.QueryValueEx(key, "CountdownTimer")
            return True
        except:
            return False

    elif system == "Darwin":  # macOS
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.countdowntimer.plist")
        return os.path.exists(plist_path)

    elif system == "Linux":
        autostart_path = os.path.expanduser("~/.config/autostart/countdowntimer.desktop")
        return os.path.exists(autostart_path)

    return False


def setup_autostart(self, enable):
    """Thiết lập hoặc gỡ bỏ tự động khởi động"""
    system = platform.system()
    app_path = get_app_path()

    if not app_path:
        QMessageBox.warning(self, "Lỗi", "Không thể xác định đường dẫn ứng dụng.")
        return False

    try:
        if system == "Windows":
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_SET_VALUE)

            if enable:
                winreg.SetValueEx(key, "CountdownTimer", 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, "CountdownTimer")
                except:
                    pass

        elif system == "Darwin":  # macOS
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.countdowntimer.plist")

            if enable:
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.countdowntimer</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                with open(plist_path, 'w') as f:
                    f.write(plist_content)
            else:
                if os.path.exists(plist_path):
                    os.remove(plist_path)

        elif system == "Linux":
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_path = os.path.join(autostart_dir, "countdowntimer.desktop")

            if enable:
                os.makedirs(autostart_dir, exist_ok=True)
                desktop_content = f"""[Desktop Entry]
Type=Application
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[en_US]=Countdown Timer
Name=Countdown Timer
Comment[en_US]=Start Countdown Timer on system boot
Comment=Start Countdown Timer on system boot
"""
                with open(desktop_path, 'w') as f:
                    f.write(desktop_content)
            else:
                if os.path.exists(desktop_path):
                    os.remove(desktop_path)

        return True
    except Exception as e:
        QMessageBox.warning(self, "Lỗi", f"Không thể thiết lập tự động khởi động: {str(e)}")
        return False


def get_app_path():
    """Lấy đường dẫn đến ứng dụng"""
    if getattr(sys, 'frozen', False):
        # Đây là đường dẫn khi ứng dụng đã được đóng gói
        return sys.executable
    else:
        # Đây là đường dẫn khi chạy từ script
        return os.path.abspath(sys.argv[0])