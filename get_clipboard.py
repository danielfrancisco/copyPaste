import subprocess

def get_clipboard_function():
    """
    Retrieve clipboard text synchronously using xclip.
    """
    try:
        result = subprocess.run(
            ['xclip', '-selection', 'clipboard', '-o'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None

