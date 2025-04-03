# Apx Performance Automation

This repository contains a Python script to automate the process of cloning a runtime repository, building it, running SuperPMI, and generating visual representations of performance differences.

## Features

- Clones the runtime repository and checks out a specific branch.
- Builds the runtime and tests.
- Runs SuperPMI to generate performance comparison data.
- Creates a graph visualizing "Diff Instruction Count" by method.

## Prerequisites

Before running the script, ensure the following dependencies are installed:

### System Requirements

1. **Python 3.7 or higher**:
   - Download and install Python from [python.org](https://www.python.org/downloads/).
   - Ensure Python is added to your system's `PATH`.

2. **Git**:
   - Download and install Git from [git-scm.com](https://git-scm.com/).

3. **C++ Build Tools**:
   - Install the required build tools for your platform:
     - On Windows: Install the "Build Tools for Visual Studio" from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
     - On Linux: Install `build-essential` and other required packages.
     - On macOS: Install Xcode Command Line Tools.

### Python Dependencies

The script requires the following Python libraries:

- `matplotlib`: For generating graphs.
- `pandas`: For processing tabular data.

Install these dependencies using `pip`:
```bash
pip install matplotlib pandas

Repository Structure
DownloadRepoAndRunTest.py: The main script to automate the process.
runResults/: Folder where results (base and diffAPX) and graphs are stored.
runtime/: The cloned runtime repository.
Usage
Clone this repository:

Run the script:

The script will:

Clone the runtime repository.
Build the runtime and tests.
Run SuperPMI to generate diff_short_summary.md.
Create a graph showing "Diff Instruction Count" by method.
Results:

The runResults folder will contain:
base/: The baseline build.
diffAPX/: The modified build.
diff_instruction_count_graph.png: A graph visualizing the results.
Troubleshooting
pip is not recognized
Ensure Python and Pip are added to your system's PATH. Refer to the Python installation guide.

SSL: CERTIFICATE_VERIFY_FAILED
Run the following command to bypass SSL verification:

Missing Build Tools
Ensure you have installed the required build tools for your platform (e.g., Visual Studio Build Tools on Windows).

License
This project is licensed under the MIT License. See the LICENSE file for details