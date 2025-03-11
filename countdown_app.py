import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTimeEdit,
                             QMenu, QSystemTrayIcon, QDialog, QSlider, QSpinBox,
                             QGroupBox, QFormLayout, QMessageBox, QStyle)  # Thêm QStyle
from PyQt6.QtCore import Qt, QTimer, QTime, QDateTime, pyqtSignal, QSettings
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

        # Nhóm cài đặt font size
        fontSizeGroup = QGroupBox("Kích thước chữ")
        fontSizeLayout = QFormLayout()

        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setRange(10, 100)
        self.fontSizeSpinBox.setValue(self.settings.value("fontSize", 26, int))
        fontSizeLayout.addRow("Kích thước chữ:", self.fontSizeSpinBox)

        fontSizeGroup.setLayout(fontSizeLayout)
        layout.addWidget(fontSizeGroup)

        # Nhóm thời gian mặc định
        timeGroup = QGroupBox("Thời gian làm việc mặc định")
        timeLayout = QFormLayout()

        self.hoursSpinBox = QSpinBox()
        self.hoursSpinBox.setRange(0, 24)
        self.hoursSpinBox.setValue(self.settings.value("defaultHours", 9, int))
        timeLayout.addRow("Giờ:", self.hoursSpinBox)

        self.minutesSpinBox = QSpinBox()
        self.minutesSpinBox.setRange(0, 59)
        self.minutesSpinBox.setValue(self.settings.value("defaultMinutes", 48, int))
        timeLayout.addRow("Phút:", self.minutesSpinBox)

        timeGroup.setLayout(timeLayout)
        layout.addWidget(timeGroup)

        # Cài đặt tự động khởi động lại
        restartGroup = QGroupBox("Tự động khởi động lại")
        restartLayout = QFormLayout()

        self.autoRestartSpinBox = QSpinBox()
        self.autoRestartSpinBox.setRange(0, 60)
        self.autoRestartSpinBox.setValue(self.settings.value("autoRestart", 0, int))
        self.autoRestartSpinBox.setSpecialValueText("Tắt")
        restartLayout.addRow("Khởi động lại sau (phút):", self.autoRestartSpinBox)

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
        self.settings.setValue("defaultHours", self.hoursSpinBox.value())
        self.settings.setValue("defaultMinutes", self.minutesSpinBox.value())
        self.settings.setValue("autoRestart", self.autoRestartSpinBox.value())
        self.accept()


class CountdownTimer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Cài đặt
        self.settings = QSettings("CountdownApp", "Timer")

        # Thời gian làm việc mặc định (từ cài đặt)
        self.loadWorkingTime()

        # Khởi tạo timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateTimer)

        # Set isCompactMode before initializing system tray
        self.isCompactMode = False

        # System tray
        self.initSystemTray()

        # Khởi tạo giao diện
        self.initUI()

        # Thời gian kết thúc và thời gian còn lại
        self.endTime = None
        self.remainingTime = 0
        self.isRunning = False

        # Tính toán thời gian ra dựa trên giờ vào
        self.calculateEndTime()

        # Chỉ hiển thị nút đóng (loại bỏ nút phóng to và thu nhỏ)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

    def loadWorkingTime(self):
        # Đọc thời gian làm việc từ cài đặt
        hours = self.settings.value("defaultHours", 9, int)
        minutes = self.settings.value("defaultMinutes", 48, int)
        self.workingTimeSeconds = hours * 3600 + minutes * 60

    def calculateEndTime(self):
        # Lấy giờ vào từ spin boxes
        if hasattr(self, 'hourSpinBox') and hasattr(self, 'minuteSpinBox'):
            startHours = self.hourSpinBox.value()
            startMinutes = self.minuteSpinBox.value()

            # Chuyển đổi thời gian làm việc từ giây sang giờ và phút
            workHours = self.workingTimeSeconds // 3600
            workMinutes = (self.workingTimeSeconds % 3600) // 60

            # Tính thời gian kết thúc
            endHours = (startHours + workHours + (startMinutes + workMinutes) // 60) % 24
            endMinutes = (startMinutes + workMinutes) % 60

            # Hiển thị thông tin giờ ra
            if hasattr(self, 'endTimeLabel'):
                self.endTimeLabel.setText(f"Giờ ra: {endHours:02d}:{endMinutes:02d}")

            # Tạo QTime cho thời điểm kết thúc
            self.calculatedEndTime = QTime(endHours, endMinutes)

            # Cập nhật tiêu đề cửa sổ
            self.setWindowTitle(f"Đếm ngược - Hết giờ lúc: {endHours:02d}:{endMinutes:02d}")

            # Tính thời gian còn lại từ hiện tại đến giờ ra
            self.calculateRemainingTime()

    def calculateRemainingTime(self):
        # Nếu chưa có thời gian kết thúc, không làm gì cả
        if not hasattr(self, 'calculatedEndTime'):
            return

        # Lấy thời gian hiện tại
        currentTime = QTime.currentTime()

        # Tạo QDateTime cho ngày hiện tại với thời gian hiện tại và thời gian kết thúc
        currentDateTime = QDateTime.currentDateTime()

        endDateTime = QDateTime(currentDateTime.date(), self.calculatedEndTime)

        # Nếu thời gian kết thúc đã qua trong ngày hôm nay, đặt nó vào ngày mai
        if self.calculatedEndTime < currentTime:
            endDateTime = endDateTime.addDays(1)

        # Tính số giây còn lại
        self.remainingTime = currentDateTime.secsTo(endDateTime)

        # Cập nhật hiển thị
        self.updateDisplay()

    def initUI(self):
        self.setWindowTitle("Đếm ngược thời gian")

        # Widget chính
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        self.mainLayout = QVBoxLayout(centralWidget)
        self.mainLayout.setSpacing(5)  # Giảm khoảng cách giữa các phần tử

        # Container cho phần cài đặt thời gian
        self.settingsContainer = QWidget()
        settingsLayout = QVBoxLayout(self.settingsContainer)
        settingsLayout.setSpacing(5)  # Giảm khoảng cách
        settingsLayout.setContentsMargins(0, 0, 0, 0)  # Giảm lề

        # Thời gian khởi đầu - Sử dụng 2 ô nhập riêng biệt cho giờ và phút
        startTimeLayout = QHBoxLayout()
        startTimeLayout.setSpacing(5)  # Giảm khoảng cách
        startTimeLabel = QLabel("Giờ vào:")

        # SpinBox cho giờ
        self.hourSpinBox = QSpinBox()
        self.hourSpinBox.setRange(0, 23)
        self.hourSpinBox.setValue(QTime.currentTime().hour())
        self.hourSpinBox.setWrapping(True)
        self.hourSpinBox.valueChanged.connect(self.calculateEndTime)

        # Label giữa hai spinbox
        hourMinuteLabel = QLabel(":")

        # SpinBox cho phút
        self.minuteSpinBox = QSpinBox()
        self.minuteSpinBox.setRange(0, 59)
        self.minuteSpinBox.setValue(QTime.currentTime().minute())
        self.minuteSpinBox.setWrapping(True)
        self.minuteSpinBox.valueChanged.connect(self.calculateEndTime)

        # Nút thời gian hiện tại
        currentTimeButton = QPushButton("Hiện tại")
        currentTimeButton.clicked.connect(self.setCurrentTime)

        startTimeLayout.addWidget(startTimeLabel)
        startTimeLayout.addWidget(self.hourSpinBox)
        startTimeLayout.addWidget(hourMinuteLabel)
        startTimeLayout.addWidget(self.minuteSpinBox)
        startTimeLayout.addWidget(currentTimeButton)
        settingsLayout.addLayout(startTimeLayout)

        # Hiển thị thời gian kết thúc
        self.endTimeLabel = QLabel("Giờ ra: --:--", alignment=Qt.AlignmentFlag.AlignCenter)
        settingsLayout.addWidget(self.endTimeLabel)

        # Nút điều khiển
        controlLayout = QHBoxLayout()
        controlLayout.setSpacing(5)  # Giảm khoảng cách

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

        settingsLayout.addLayout(controlLayout)
        self.mainLayout.addWidget(self.settingsContainer)

        # Hiển thị thời gian đếm ngược
        self.timeLabel = QLabel("00:00:00", alignment=Qt.AlignmentFlag.AlignCenter)
        self.updateFontSize()
        self.mainLayout.addWidget(self.timeLabel)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        # Thiết lập kích thước cửa sổ ban đầu
        self.normalSize = (250, 150)
        self.compactSize = (100, 50)
        self.resize(*self.normalSize)

        # Tính toán thời gian kết thúc dựa trên giờ vào hiện tại
        self.calculateEndTime()

    def setCurrentTime(self):
        currentTime = QTime.currentTime()
        self.hourSpinBox.setValue(currentTime.hour())
        self.minuteSpinBox.setValue(currentTime.minute())

    def updateFontSize(self):
        fontSize = self.settings.value("fontSize", 26, int)
        # Nếu ở chế độ compact, giảm kích thước chữ
        if self.isCompactMode:
            fontSize = int(fontSize * 0.7)  # Giảm 30% kích thước chữ ở chế độ compact

        font = QFont()
        font.setPointSize(fontSize)
        font.setBold(True)
        self.timeLabel.setFont(font)

        # Điều chỉnh kích thước cửa sổ dựa trên kích thước font
        fontMetrics = QFontMetrics(font)
        textWidth = fontMetrics.horizontalAdvance("00:00:00")

        if self.isCompactMode:
            self.setMinimumWidth(textWidth + 20)
        else:
            self.setMinimumWidth(max(textWidth + 40, 250))

    def toggleCompactMode(self, compact=None):
        # Nếu không có tham số, đảo ngược trạng thái hiện tại
        if compact is None:
            self.isCompactMode = not self.isCompactMode
        else:
            self.isCompactMode = compact

        # Ẩn hoặc hiện phần cài đặt
        self.settingsContainer.setVisible(not self.isCompactMode)

        # Cập nhật kích thước font trước
        self.updateFontSize()

        # Cập nhật cờ cửa sổ
        if self.isCompactMode:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
            if hasattr(self, 'calculatedEndTime'):
                self.setWindowTitle(f"Đếm ngược - Hết giờ lúc: {self.calculatedEndTime.toString('hh:mm')}")

        # Giữ tham chiếu đến vị trí hiện tại
        currentPos = self.pos()

        # Hiển thị lại cửa sổ sau khi thay đổi cờ
        self.show()

        # Đảm bảo Qt đã xử lý sự kiện show và cập nhật kích thước của timeLabel
        QApplication.processEvents()

        # Điều chỉnh kích thước dựa trên trạng thái
        if self.isCompactMode:
            # Tính toán kích thước chỉ vừa đủ cho timeLabel
            width = self.timeLabel.sizeHint().width() + 20
            height = self.timeLabel.sizeHint().height() + 10
            self.resize(width, height)
        else:
            # Sử dụng kích thước bình thường cho chế độ đầy đủ
            self.resize(*self.normalSize)

        # Đặt lại vị trí để tránh cửa sổ bị nhảy
        self.move(currentPos)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPosition)
            event.accept()

    def initSystemTray(self):
        # Tạo system tray icon
        self.trayIcon = QSystemTrayIcon(self)

        # Thêm một biểu tượng mặc định cho tray icon
        # Thay đổi đường dẫn này đến một tệp icon thực tế
        # Nếu không có icon, có thể sử dụng biểu tượng mặc định của ứng dụng
        # self.trayIcon.setIcon(QIcon("path/to/your/icon.png"))
        self.trayIcon.setIcon(
            QIcon.fromTheme("clock", QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)))

        self.trayIcon.setToolTip("Đếm ngược thời gian")

        # Kết nối sự kiện khi nhấp vào biểu tượng
        self.trayIcon.activated.connect(self.trayIconActivated)

        # Tạo menu cho system tray
        trayMenu = QMenu()

        # Menu code...

        self.trayIcon.setContextMenu(trayMenu)
        # Đảm bảo hiển thị icon
        self.trayIcon.show()

    def trayIconActivated(self, reason):
        # Xử lý khi người dùng nhấp vào biểu tượng khay hệ thống
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Click đơn
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()  # Đưa cửa sổ lên trên

    def closeEvent(self, event):
        # Kiểm tra xem có thoát hoàn toàn hay chỉ ẩn vào khay hệ thống
        if self.trayIcon.isVisible():
            # Nếu icon đã được hiển thị trong khay hệ thống
            QMessageBox.information(
                self, "Đếm ngược thời gian",
                "Ứng dụng vẫn chạy ở khay hệ thống. "
                "Để thoát hoàn toàn, hãy nhấp chuột phải vào biểu tượng trong "
                "khay hệ thống và chọn 'Thoát'."
            )
            # Ẩn cửa sổ thay vì đóng
            self.hide()
            event.ignore()
        else:
            # Hỏi người dùng xác nhận thoát nếu không có biểu tượng khay
            reply = QMessageBox.question(
                self, 'Thoát',
                "Bạn có chắc chắn muốn thoát?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()


    def showContextMenu(self, pos):
        contextMenu = QMenu(self)

        toggleModeAction = QAction("Chế độ nhỏ gọn", self)
        toggleModeAction.setCheckable(True)
        toggleModeAction.setChecked(self.isCompactMode)
        toggleModeAction.triggered.connect(self.toggleCompactMode)
        contextMenu.addAction(toggleModeAction)

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
        flags = Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)
        self.show()

    def openSettings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.updateFontSize()
            self.loadWorkingTime()
            self.calculateEndTime()


    def startTimer(self):
        if not self.isRunning:
            # Tính lại thời gian còn lại từ thời điểm hiện tại đến giờ ra
            self.calculateRemainingTime()

            # Bắt đầu đếm ngược
            self.timer.start(1000)  # Cập nhật mỗi giây
            self.isRunning = True
            self.startButton.setEnabled(False)
            self.pauseButton.setEnabled(True)
            self.hourSpinBox.setEnabled(False)
            self.minuteSpinBox.setEnabled(False)

            # Chuyển sang chế độ nhỏ gọn
            self.isCompactMode = True
            self.settingsContainer.setVisible(False)
            self.updateFontSize()

            # Áp dụng cờ cửa sổ cho chế độ nhỏ gọn
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

            # Tính toán kích thước mới
            width = self.timeLabel.sizeHint().width() + 20
            height = self.timeLabel.sizeHint().height() + 10

            # Hiển thị lại và điều chỉnh kích thước
            self.show()
            QApplication.processEvents()  # Đảm bảo UI được cập nhật
            self.resize(width, height)

            self.updateDisplay()


    def pauseTimer(self):
        if self.isRunning:
            self.timer.stop()
            self.isRunning = False
            self.startButton.setEnabled(True)
            self.pauseButton.setEnabled(False)

    def resetTimer(self):
        self.timer.stop()
        self.isRunning = False
        self.hourSpinBox.setEnabled(True)
        self.minuteSpinBox.setEnabled(True)

        # Quay về chế độ đầy đủ
        self.toggleCompactMode(False)

        # Vẫn giữ thiết lập hiển thị trên cùng
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

        self.calculateEndTime()  # Tính lại thời gian kết thúc và thời gian còn lại
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)

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
            self.hourSpinBox.setEnabled(True)
            self.minuteSpinBox.setEnabled(True)

            # Quay về chế độ đầy đủ khi hết giờ
            self.toggleCompactMode(False)

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

    # Thêm đoạn này vào
    settings = QSettings("CountdownApp", "Timer")
    if settings.contains("autostart"):
        window.set_autostart(settings.value("autostart", False, type=bool))
    # Kết thúc đoạn thêm vào

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()