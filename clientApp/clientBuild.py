from cx_Freeze import setup, Executable
import sys

# Define the build options
build_exe_options = {
    "packages": ["socket", "threading", "time", "infi.systray"],
    "include_files": ["lib/client.ico"]  # Include the icon file
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        "clientApp.py",
        base=base,
        icon="lib/client.ico",
        target_name="clientApp.exe",
    )
]

setup(
    name="clientApp",
    version="1.0",
    description="client application running in the background",
    options={"build_exe": build_exe_options},
    executables=executables
)
