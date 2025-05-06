# SuperPMI Automation Script

This script automates the process of running SuperPMI (Super Performance Measurement Infrastructure) to compare JIT (Just-In-Time) compiler performance across different configurations and branches. It also generates visual representations of the results for easier analysis.

## Features

1. **Repository Management**:
   - Clones the `runtime` repository from GitHub.
   - Checks out specific branches for testing.
   - Deletes and recreates branches locally if needed.

2. **JIT Configuration Testing**:
   - Runs SuperPMI with various JIT configurations to compare performance.
   - Supports multiple configurations for both base and diff JIT options.
   - Automatically generates unique CSV files for each configuration.

3. **Graph Generation**:
   - Reads the generated CSV files and creates bar graphs for:
     - **Instruction Count Difference**
     - **% Instruction Count Difference**
     - **% Instruction Count Difference (Ignoring Zero Diffs)**
   - Highlights key equations in the graph headers and explanations.
   - Displays values above the bars for better readability.

4. **File Management**:
   - Deletes and recreates directories as needed.
   - Copies the `Core_Root` directory for both base and diff configurations.
   - Moves SuperPMI output files to organized folders.

## How It Works

### 1. **Setup**
   - Clones the `runtime` repository from [GitHub](https://github.com/dotnet/runtime).
   - Clones the `jitutils` repository and runs `bootstrap.cmd` to set up the environment.

### 2. **Branch Processing**
   - Switches to the specified branch (e.g., `16_eGPR`) and builds the runtime and tests.
   - Copies the `Core_Root` directory for both base and diff configurations.

### 3. **SuperPMI Execution**
   - Runs the `superpmi.py` script with the following configurations:
     - **Base JIT Options**:
       - `JitBypassApxCheck=0`
       - `EnableApxNDD=0`
       - `EnableApxConditionalChaining=0`
     - **Diff JIT Options**:
       - `JitBypassApxCheck=1`, `EnableApxNDD=0`, `EnableApxConditionalChaining=0`
       - `JitBypassApxCheck=1`, `EnableApxNDD=1`, `EnableApxConditionalChaining=0`
       - `JitBypassApxCheck=1`, `EnableApxNDD=0`, `EnableApxConditionalChaining=1`
       - `JitBypassApxCheck=1`, `EnableApxNDD=1`, `EnableApxConditionalChaining=1`
   - Generates detailed CSV files for each configuration.

### 4. **Graph Generation**
   - Reads the generated CSV files and creates bar graphs for the following metrics:
     - **Instruction Count Difference**: `(Diff Instr Count - Base Instr Count)`
     - **% Instruction Count Difference**: `((Diff Instr Count - Base Instr Count) * 100) / Base Instr Count`
     - **% Instruction Count Difference (Ignoring Zero Diffs)**: `((Diff Instr Count - Base Instr Count) * 100) / Base Instr Count for only methods with diff`
   - Adds explanations and highlights equations in the graph headers.
   - Saves the graphs as PNG files.

## Prerequisites

1. **Python**:
   - Ensure Python is installed and available in your system's PATH.

2. **Git**:
   - Ensure Git is installed and available in your system's PATH.

3. **Dependencies**:
   - The script uses the following Python libraries:
     - `subprocess`
     - `os`
     - `shutil`
     - `matplotlib`
     - `pandas`
     - `json`

   Install the required libraries using:
   ```bash
   pip install matplotlib pandas