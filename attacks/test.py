import subprocess

# Full path to karma_attack.py
path_to_script = "/home/ahmad/Programming/AirStrike/attacks/karma_attack.py"

# Create the subprocess
process = subprocess.Popen(
    ["python3", path_to_script, "wlan0"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)


# Print stdout line by line in real time
for line in process.stdout:
    print(line, end='')

# Wait for it to complete
process.wait()
