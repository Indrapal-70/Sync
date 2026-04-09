import subprocess
import os
import sys

WORKSPACE = "/home/inder/autoforge/workspace"
SRC = f"{WORKSPACE}/src"

def run() -> bool:
    print("[TESTER] Installing dependencies...")

    # Install requirements if they exist
    req_file = f"{SRC}/requirements.txt"
    if os.path.exists(req_file):
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file, "-q"],
            cwd=SRC
        )

    print("[TESTER] Running pytest...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd=SRC
    )

    output = result.stdout + result.stderr
    passed = result.returncode == 0

    # Write test results
    with open(f"{WORKSPACE}/test_results.txt", "w") as f:
        f.write(output)

    with open(f"{WORKSPACE}/logs/tester.log", "a") as f:
        f.write(f"[TESTER] {'PASSED' if passed else 'FAILED'}\n{output}\n")

    if passed:
        with open(f"{WORKSPACE}/status.txt", "w") as f:
            f.write("TESTS_PASSED")
        print("[TESTER] All tests passed")
    else:
        # Write error trace for debugger
        with open(f"{WORKSPACE}/errors/test_errors.txt", "w") as f:
            f.write(output)
        with open(f"{WORKSPACE}/status.txt", "w") as f:
            f.write("TESTS_FAILED")
        print("[TESTER] Tests failed — error trace written to workspace/errors/")

    print(output)
    return passed

if __name__ == "__main__":
    run()
