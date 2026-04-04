#!/usr/bin/env python3
"""
GUI Wrapper for Smart Text-on-Video Overlay Tool

Provides a simple graphical interface for the smart overlay tool using PyQt5.
"""

import os
import sys
import subprocess
import threading
from pathlib import Path
from typing import List, Optional

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QLineEdit, QFileDialog, QComboBox,
        QTextEdit, QProgressBar, QGroupBox, QFormLayout, QCheckBox,
        QMessageBox, QTabWidget
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
    from PyQt5.QtGui import QIcon, QFont
except ImportError:
    print("PyQt5 is required for the GUI. Install it with: pip install PyQt5")
    sys.exit(1)

# Add this to requirements.txt if using GUI
# PyQt5>=5.15.0


class WorkerThread(QThread):
    """Worker thread for running the smart overlay process."""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, command: List[str]):
        super().__init__()
        self.command = command

    def run(self):
        """Run the command and emit signals with output."""
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line
            for line in iter(process.stdout.readline, ''):
                self.update_signal.emit(line.strip())

            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                self.finished_signal.emit(True, "Processing completed successfully!")
            else:
                self.finished_signal.emit(False, f"Processing failed with return code {return_code}")
        
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")


class SmartOverlayGUI(QMainWindow):
    """Main GUI window for the Smart Text-on-Video Overlay Tool."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Smart Text-on-Video Overlay Tool")
        self.setMinimumSize(800, 600)

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Create tabs for different sections
        process_tab = QWidget()
        settings_tab = QWidget()
        logs_tab = QWidget()

        tabs.addTab(process_tab, "Process Videos")
        tabs.addTab(settings_tab, "Settings")
        tabs.addTab(logs_tab, "Logs")

        # Process tab layout
        process_layout = QVBoxLayout()
        process_tab.setLayout(process_layout)

        # Input directory selection
        input_group = QGroupBox("Input Videos")
        input_layout = QFormLayout()
        input_group.setLayout(input_layout)

        self.input_dir = QLineEdit()
        browse_input_btn = QPushButton("Browse...")
        browse_input_btn.clicked.connect(self.browse_input_dir)

        input_dir_layout = QHBoxLayout()
        input_dir_layout.addWidget(self.input_dir)
        input_dir_layout.addWidget(browse_input_btn)
        input_layout.addRow("Input Directory:", input_dir_layout)

        process_layout.addWidget(input_group)

        # Prompt settings
        prompt_group = QGroupBox("Prompt Settings")
        prompt_layout = QFormLayout()
        prompt_group.setLayout(prompt_layout)

        self.prompt_text = QLineEdit()
        prompt_layout.addRow("Prompt:", self.prompt_text)

        self.batch_prompts_file = QLineEdit()
        browse_prompts_btn = QPushButton("Browse...")
        browse_prompts_btn.clicked.connect(self.browse_prompts_file)

        batch_prompts_layout = QHBoxLayout()
        batch_prompts_layout.addWidget(self.batch_prompts_file)
        batch_prompts_layout.addWidget(browse_prompts_btn)
        
        self.use_batch_prompts = QCheckBox("Use batch prompts file")
        prompt_layout.addRow(self.use_batch_prompts, batch_prompts_layout)

        process_layout.addWidget(prompt_group)

        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QFormLayout()
        font_group.setLayout(font_layout)

        self.font_preset = QComboBox()
        self.font_preset.addItems(["TechMeStuff", "Minimalist", "Dramatic", "Professional"])
        font_layout.addRow("Font Preset:", self.font_preset)

        self.custom_font = QLineEdit()
        browse_font_btn = QPushButton("Browse...")
        browse_font_btn.clicked.connect(self.browse_font_file)

        custom_font_layout = QHBoxLayout()
        custom_font_layout.addWidget(self.custom_font)
        custom_font_layout.addWidget(browse_font_btn)
        
        self.use_custom_font = QCheckBox("Use custom font")
        font_layout.addRow(self.use_custom_font, custom_font_layout)

        process_layout.addWidget(font_group)

        # API Key
        api_group = QGroupBox("OpenAI API Key")
        api_layout = QFormLayout()
        api_group.setLayout(api_layout)

        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        api_layout.addRow("API Key:", self.api_key)

        process_layout.addWidget(api_group)

        # Process button
        self.process_btn = QPushButton("Process Videos")
        self.process_btn.setMinimumHeight(50)
        self.process_btn.clicked.connect(self.process_videos)
        process_layout.addWidget(self.process_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        process_layout.addWidget(self.progress_bar)

        # Settings tab
        settings_layout = QVBoxLayout()
        settings_tab.setLayout(settings_layout)

        # Output directory
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout()
        output_group.setLayout(output_layout)

        self.output_dir = QLineEdit("./outputs")
        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(self.browse_output_dir)

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir)
        output_dir_layout.addWidget(browse_output_btn)
        output_layout.addRow("Output Directory:", output_dir_layout)

        # Config file
        self.config_file = QLineEdit("./config.yaml")
        browse_config_btn = QPushButton("Browse...")
        browse_config_btn.clicked.connect(self.browse_config_file)

        config_file_layout = QHBoxLayout()
        config_file_layout.addWidget(self.config_file)
        config_file_layout.addWidget(browse_config_btn)
        output_layout.addRow("Config File:", config_file_layout)

        settings_layout.addWidget(output_group)

        # Font download button
        download_fonts_btn = QPushButton("Download Required Fonts")
        download_fonts_btn.clicked.connect(self.download_fonts)
        settings_layout.addWidget(download_fonts_btn)

        settings_layout.addStretch()

        # Logs tab
        logs_layout = QVBoxLayout()
        logs_tab.setLayout(logs_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        logs_layout.addWidget(self.log_output)

        # Clear logs button
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        logs_layout.addWidget(clear_logs_btn)

    def browse_input_dir(self):
        """Open file dialog to select input directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if dir_path:
            self.input_dir.setText(dir_path)

    def browse_output_dir(self):
        """Open file dialog to select output directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir.setText(dir_path)

    def browse_prompts_file(self):
        """Open file dialog to select prompts file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Prompts File", "", "Text Files (*.txt)")
        if file_path:
            self.batch_prompts_file.setText(file_path)
            self.use_batch_prompts.setChecked(True)

    def browse_font_file(self):
        """Open file dialog to select font file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Font File", "", "Font Files (*.ttf *.otf)")
        if file_path:
            self.custom_font.setText(file_path)
            self.use_custom_font.setChecked(True)

    def browse_config_file(self):
        """Open file dialog to select config file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Config File", "", "YAML Files (*.yaml *.yml)")
        if file_path:
            self.config_file.setText(file_path)

    def clear_logs(self):
        """Clear the log output."""
        self.log_output.clear()

    def download_fonts(self):
        """Download required fonts."""
        try:
            from utils.font_downloader import download_and_install_fonts
            
            # Run in a separate thread to avoid freezing the UI
            def run_download():
                try:
                    download_and_install_fonts()
                    self.log_output.append("Fonts downloaded successfully!")
                except Exception as e:
                    self.log_output.append(f"Error downloading fonts: {str(e)}")
            
            threading.Thread(target=run_download).start()
            
        except ImportError:
            self.log_output.append("Error: Font downloader module not found.")
            QMessageBox.warning(self, "Error", "Font downloader module not found.")

    def update_log(self, text):
        """Update the log output with new text."""
        self.log_output.append(text)
        # Scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def process_complete(self, success, message):
        """Handle process completion."""
        self.progress_bar.hide()
        self.process_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)

    def process_videos(self):
        """Process videos with the smart overlay tool."""
        # Validate inputs
        if not self.input_dir.text():
            QMessageBox.warning(self, "Error", "Please select an input directory.")
            return
        
        if not self.prompt_text.text() and not (self.use_batch_prompts.isChecked() and self.batch_prompts_file.text()):
            QMessageBox.warning(self, "Error", "Please enter a prompt or select a batch prompts file.")
            return
        
        if not self.api_key.text():
            QMessageBox.warning(self, "Error", "Please enter your OpenAI API key.")
            return
        
        # Build command
        cmd = [
            "python", "smart_overlay.py",
            "--input_dir", self.input_dir.text(),
            "--output_dir", self.output_dir.text(),
            "--config", self.config_file.text(),
            "--preset", self.font_preset.currentText(),
            "--openai_key", self.api_key.text()
        ]
        
        # Add prompt
        if self.prompt_text.text():
            cmd.extend(["--prompt", self.prompt_text.text()])
        
        # Add batch prompts if selected
        if self.use_batch_prompts.isChecked() and self.batch_prompts_file.text():
            cmd.extend(["--batch_prompts", self.batch_prompts_file.text()])
        
        # Add custom font if selected
        if self.use_custom_font.isChecked() and self.custom_font.text():
            cmd.extend(["--font_path", self.custom_font.text()])
        
        # Show progress bar and disable process button
        self.progress_bar.show()
        self.process_btn.setEnabled(False)
        
        # Clear logs
        self.log_output.clear()
        
        # Start worker thread
        self.worker = WorkerThread(cmd)
        self.worker.update_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.process_complete)
        self.worker.start()


def main():
    """Main entry point for the GUI."""
    app = QApplication(sys.argv)
    window = SmartOverlayGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
