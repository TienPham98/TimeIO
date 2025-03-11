import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTimeEdit,
                             QMenu, QSystemTrayIcon, QDialog, QSlider, QSpinBox,
                             QGroupBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QIcon, QFont, QFontMetrics


class NotificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Thông báo")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # Thông báo hết giờ
        self.label = QLabel("HẾT GIỜ!", alignment=Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.label.setFont(font)
        layout.addWidget(self.label)

        # Nút đóng
        self.closeButton = QPushButton("Đóng")
        self.closeButton.clicked.connect(self.accept)
        layout.addWidget(self.closeButton)

        self.setLayout(layout)


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Cài đặt")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Kích thước font
        fontGroup = QGroupBox("Kích thước font")
        fontLayout = QFormLayout()

        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setRange(8, 72)
        self.fontSizeSpinBox.setValue(self.settings.value("fontSize", 40, int))
        fontLayout.addRow("Kích thước:", self.fontSizeSpinBox)

        fontGroup.setLayout(fontLayout)
        layout.addWidget(fontGroup)

        # Tự động khởi động lại
        restartGroup = QGroupBox("Tự động khởi động lại")
        restartLayout = QFormLayout()

        self.autoRestartSpinBox = QSpinBox()
        self.autoRestartSpinBox.setRange(0, 60)
        self.autoRestartSpinBox.setValue(self.settings.value("autoRestart", 0, int))
        self.autoRestartSpinBox.setSuffix(" phút (0 = tắt)")
        restartLayout.addRow("Khởi động lại sau:", self.autoRestartSpinBox)

        restartGroup.setLayout(restartLayout)
        layout.addWidget(restartGroup)

        # Nút lưu và hủy
        buttonLayout = QHBoxLayout()
        saveButton = QPushButton("Lưu")
        saveButton.clicked.connect(self.saveSettings)
        cancelButton = QPushButton("Hủy")
        cancelButton.clicked.connect(self.reject)

        buttonLayout.addWidget(saveButton)
        buttonLayout.addWidget(cancelButton)
        layout.addLayout(buttonLayout)

        self.setLayout(layout)

    def saveSettings(self):
        self.settings.setValue("fontSize", self.fontSizeSpinBox.value())
        self.settings.setValue("autoRestart", self.autoRestartSpinBox.value())
        self.accept()


class CountdownTimer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Cài đặt
        self.settings = QSettings("CountdownApp", "Timer")

        # Khởi tạo giao diện
        self.initUI()

        # Khởi tạo timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateTimer)

        # Thời gian còn lại (mặc định 9h48p = 35280 giây)
        self.defaultTime = 9 * 3600 + 48 * 60  # 9h48p in seconds
        self.remainingTime = self.defaultTime
        self.isRunning = False

        # System tray
        self.initSystemTray()

    def initUI(self):
        self.setWindowTitle("Đếm ngược thời gian")

        # Widget chính
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        # Thời gian khởi đầu
        startTimeLayout = QHBoxLayout()
        startTimeLabel = QLabel("Thời gian bắt đầu:")
        self.timeEdit = QTimeEdit()
        self.timeEdit.setDisplayFormat("hh:mm:ss")
        self.timeEdit.setTime(QTime(9, 48, 0))  # Mặc định 9h48p

        startTimeLayout.addWidget(startTimeLabel)
        startTimeLayout.addWidget(self.timeEdit)
        mainLayout.addLayout(startTimeLayout)

        # Hiển thị thời gian đếm ngược
        self.timeLabel = QLabel("09:48:00", alignment=Qt.AlignmentFlag.AlignCenter)
        self.updateFontSize()
        mainLayout.addWidget(self.timeLabel)

        # Nút điều khiển
        controlLayout = QHBoxLayout()

        self.startButton = QPushButton("Start")
        self.startButton.clicked.connect(self.startTimer)

        self.pauseButton = QPushButton("Pause")
        self.pauseButton.clicked.connect(self.pauseTimer)
        self.pauseButton.setEnabled(False)

        self.resetButton = QPushButton("Reset")
        self.resetButton.clicked.connect(self.resetTimer)

        controlLayout.addWidget(self.startButton)
        controlLayout.addWidget(self.pauseButton)
        controlLayout.addWidget(self.resetButton)

        mainLayout.addLayout(controlLayout)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        # Thiết lập kích thước cửa sổ
        self.resize(300, 200)

    def updateFontSize(self):
        fontSize = self.settings.value("fontSize", 40, int)
        font = QFont()
        font.setPointSize(fontSize)
        font.setBold(True)
        self.timeLabel.setFont(font)

        # Điều chỉnh kích thước cửa sổ dựa trên kích thước font
        fontMetrics = QFontMetrics(font)
        textWidth = fontMetrics.horizontalAdvance("00:00:00")
        self.setMinimumWidth(textWidth + 40)

    def initSystemTray(self):
        # Tạo system tray icon
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setToolTip("Đếm ngược thời gian")

        # Tạo menu cho system tray
        trayMenu = QMenu()

        showAction = QAction("Hiện", self)
        showAction.triggered.connect(self.show)

        hideAction = QAction("Ẩn", self)
        hideAction.triggered.connect(self.hide)

        settingsAction = QAction("Cài đặt", self)
        settingsAction.triggered.connect(self.openSettings)

        quitAction = QAction("Thoát", self)
        quitAction.triggered.connect(self.close)

        trayMenu.addAction(showAction)
        trayMenu.addAction(hideAction)
        trayMenu.addAction(settingsAction)
        trayMenu.addSeparator()
        trayMenu.addAction(quitAction)

        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)

        settingsAction = QAction("Cài đặt", self)
        settingsAction.triggered.connect(self.openSettings)
        contextMenu.addAction(settingsAction)

        alwaysOnTopAction = QAction("Luôn hiển thị trên cùng", self)
        alwaysOnTopAction.setCheckable(True)
        alwaysOnTopAction.setChecked(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
        alwaysOnTopAction.triggered.connect(self.toggleAlwaysOnTop)
        contextMenu.addAction(alwaysOnTopAction)

        minimizeToTrayAction = QAction("Thu nhỏ vào khay hệ thống", self)
        minimizeToTrayAction.triggered.connect(self.hide)
        contextMenu.addAction(minimizeToTrayAction)

        contextMenu.addSeparator()

        quitAction = QAction("Thoát", self)
        quitAction.triggered.connect(self.close)
        contextMenu.addAction(quitAction)

        contextMenu.exec(self.mapToGlobal(pos))

    def toggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def openSettings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.updateFontSize()

    def startTimer(self):
        if not self.isRunning:
            # Lấy thời gian từ timeEdit nếu người dùng đã chọn
            if self.remainingTime == self.defaultTime:
                time = self.timeEdit.time()
                hours = time.hour()
                minutes = time.minute()
                seconds = time.second()
                self.remainingTime = hours * 3600 + minutes * 60 + seconds

            self.timer.start(1000)  # Cập nhật mỗi giây
            self.isRunning = True
            self.startButton.setEnabled(False)
            self.pauseButton.setEnabled(True)
            self.timeEdit.setEnabled(False)

    def pauseTimer(self):
        if self.isRunning:
            self.timer.stop()
            self.isRunning = False
            self.startButton.setEnabled(True)
            self.pauseButton.setEnabled(False)

    def resetTimer(self):
        self.timer.stop()
        self.isRunning = False
        self.remainingTime = self.defaultTime
        self.updateDisplay()
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.timeEdit.setEnabled(True)

    def updateTimer(self):
        if self.remainingTime > 0:
            self.remainingTime -= 1
            self.updateDisplay()
        else:
            self.timer.stop()
            self.isRunning = False
            self.showNotification()
            self.startButton.setEnabled(True)
            self.pauseButton.setEnabled(False)
            self.timeEdit.setEnabled(True)

            # Kiểm tra tự động khởi động lại
            autoRestart = self.settings.value("autoRestart", 0, int)
            if autoRestart > 0:
                QTimer.singleShot(autoRestart * 60 * 1000, self.resetAndStart)

    def resetAndStart(self):
        self.resetTimer()
        self.startTimer()

    def updateDisplay(self):
        hours = self.remainingTime // 3600
        minutes = (self.remainingTime % 3600) // 60
        seconds = self.remainingTime % 60
        timeString = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timeLabel.setText(timeString)
        self.trayIcon.setToolTip(f"Đếm ngược: {timeString}")

    def showNotification(self):
        dialog = NotificationDialog(self)
        dialog.exec()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Thoát',
                                     "Bạn có chắc chắn muốn thoát?",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Không thoát khi đóng cửa sổ

    window = CountdownTimer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()