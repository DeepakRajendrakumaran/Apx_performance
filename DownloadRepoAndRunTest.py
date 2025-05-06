import subprocess
import sys
import os
import shutil  # Import shutil for file operations
import matplotlib.pyplot as plt  # Import matplotlib for graphing
import pandas as pd  # Import pandas for data processing
import json  # Import json for reading JSON files


#python C:\deepak\Apx_performance\runtime\src\coreclr\scripts\superpmi.py asmdiffs -details C:\deepak\Apx_performance\runResults\diffAPX_details.csv -base_jit_path C:\deepak\Apx_performance\runResults\base\clrjit.dll -diff_jit_path C:\deepak\Apx_performance\runResults\diffAPX\clrjit.dll -diff_jit_option JitBypassApxCheck=1
# Define the repository URL and the desired directory name
REPO_URL = "https://github.com/DeepakRajendrakumaran/runtime.git"
DIR_NAME = "runtime"
BRANCH_NAME = "APX_icount"
JITUTILS_REPO_URL = "https://github.com/dotnet/jitutils.git"
JITUTILS_DIR_NAME = "jitutils"

def clone_repo(repo_url, dir_name):
    print(f"Cloning repository from '{repo_url}' into directory '{dir_name}'...")
    try:
        subprocess.run(["git", "clone", repo_url, dir_name], check=True)
        print(f"Repository cloned successfully into '{dir_name}'.")
    except subprocess.CalledProcessError:
        print(f"Failed to clone the repository into '{dir_name}'.")
        sys.exit(1)

def switch_to_main(cwd):
    print("Switching to 'main' branch...")
    try:
        subprocess.run(["git", "checkout", "main"], cwd=cwd, shell=True, check=True)
        print("Switched to 'main' branch.")
    except subprocess.CalledProcessError:
        print("Failed to switch to 'main' branch. Ensure the 'main' branch exists.")
        sys.exit(1)

def delete_branch(branch_name, cwd):
    print(f"Checking if branch '{branch_name}' exists locally...")
    try:
        # Check if the branch exists locally
        result = subprocess.run(["git", "branch", "--list", branch_name], cwd=cwd, shell=True, capture_output=True, text=True)
        if branch_name in result.stdout:
            print(f"Branch '{branch_name}' exists locally. Deleting it...")
            # Switch to 'main' before deleting the branch
            switch_to_main(cwd)
            subprocess.run(["git", "branch", "-D", branch_name], cwd=cwd, shell=True, check=True)
            print(f"Branch '{branch_name}' deleted successfully.")
        else:
            print(f"Branch '{branch_name}' does not exist locally. Skipping deletion.")
    except subprocess.CalledProcessError:
        print(f"Failed to delete branch '{branch_name}'.")
        sys.exit(1)

def checkout_branch(branch_name, cwd):
    print(f"Checking out remote branch '{branch_name}' in directory '{cwd}'...")
    try:
        # Delete the branch if it exists locally
        delete_branch(branch_name, cwd)

        # Fetch all branches and check out the specified remote branch
        subprocess.run(["git", "fetch", "origin"], check=True, cwd=cwd, shell=True)
        subprocess.run(["git", "checkout", "-b", branch_name, f"origin/{branch_name}"], check=True, cwd=cwd, shell=True)
        print(f"Checked out remote branch '{branch_name}'.")
    except subprocess.CalledProcessError:
        print(f"Failed to check out remote branch '{branch_name}'.")
        sys.exit(1)

def run_command(command, cwd=None):
    print(f"Running command: {' '.join(command)} in directory '{cwd}'...")
    try:
        subprocess.run(command, check=True, cwd=cwd, shell=True)
        print(f"Command '{' '.join(command)}' executed successfully.")
    except subprocess.CalledProcessError:
        print(f"Failed to execute command: {' '.join(command)}")
        sys.exit(1)

def delete_directory_if_exists(path):
    """Delete a directory if it exists."""
    if os.path.exists(path):
        print(f"Deleting existing directory: {path}")
        try:
            shutil.rmtree(path)
            print(f"Deleted directory: {path}")
        except Exception as e:
            print(f"Failed to delete directory '{path}': {e}")
            sys.exit(1)

def copy_core_root(repo_root, destination_root, destination_name):
    # Define the source and destination paths
    core_root_path = os.path.join(repo_root, "artifacts", "tests", "coreclr", "windows.x64.Checked", "Tests", "Core_Root")
    destination_path = os.path.join(destination_root, destination_name)

    # Delete the destination directory if it exists
    delete_directory_if_exists(destination_path)

    print(f"Copying '{core_root_path}' to '{destination_path}'...")
    try:
        # Copy the directory
        shutil.copytree(core_root_path, destination_path)
        print(f"Copied '{core_root_path}' to '{destination_path}' successfully.")
    except FileNotFoundError:
        print(f"Source directory '{core_root_path}' does not exist. Ensure the build step completed successfully.")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to copy '{core_root_path}' to '{destination_path}': {e}")
        sys.exit(1)

def setup_jitutils():
    """Clone jitutils repository and run bootstrap.cmd."""
    jitutils_path = os.path.abspath(JITUTILS_DIR_NAME)
    if os.path.exists(jitutils_path):
        print(f"Directory '{jitutils_path}' already exists. Skipping cloning step.")
    else:
        print(f"Cloning jitutils repository from '{JITUTILS_REPO_URL}' into '{jitutils_path}'...")
        clone_repo(JITUTILS_REPO_URL, JITUTILS_DIR_NAME)

    # Run bootstrap.cmd
    bootstrap_cmd_path = os.path.join(jitutils_path, "bootstrap.cmd")
    if os.path.exists(bootstrap_cmd_path):
        print(f"Running bootstrap.cmd in '{jitutils_path}'...")
        run_command([bootstrap_cmd_path], cwd=jitutils_path)
    else:
        print(f"bootstrap.cmd not found in '{jitutils_path}'. Ensure the repository is cloned correctly.")
        sys.exit(1)

def run_superpmi(repo_root, destination_path, csv_prefix, diff_coreroot_path, diff_jit_options, base_jit_options):
    """Run the superpmi.py command with specified csv_prefix and diff_jit_options."""
    # Delete the artifacts\spmi directory if it exists
    spmi_path = os.path.join(repo_root, "artifacts", "spmi")
    delete_directory_if_exists(spmi_path)

    # Create a unique name for the details CSV file based on csv_prefix and diff_jit_options
    options_suffix = "_".join(option.replace("=", "_") for option in diff_jit_options)
    details_csv_path = os.path.join(destination_path, f"{csv_prefix}_{options_suffix}.csv")

    base_jit_path = os.path.join(destination_path, "base", "clrjit.dll")
    diff_jit_path = os.path.join(diff_coreroot_path, "clrjit.dll")
    superpmi_script = os.path.join(repo_root, "src", "coreclr", "scripts", "superpmi.py")

    # Build the command
    command = [
        "python", superpmi_script, "asmdiffs",
        "-details", details_csv_path,
        "-base_jit_path", base_jit_path,
        "-diff_jit_path", diff_jit_path,
    ]

    # Add all diff_jit_options to the command
    for option in base_jit_options:
        command.extend(["-base_jit_option", option])

    # Add all diff_jit_options to the command
    for option in diff_jit_options:
        command.extend(["-diff_jit_option", option])

    # Add the filter
    # command.extend(["-filter", "libraries_tests.run"])

    print(f"Running SuperPMI command: {' '.join(command)}")
    run_command(command, cwd=repo_root)

    # Copy everything except the 'mch' folder from spmi_path to a new folder in destination_path
    output_folder_name = os.path.splitext(os.path.basename(details_csv_path))[0]  # Remove .md or .csv extension
    output_folder_path = os.path.join(destination_path, output_folder_name)

    if not os.path.exists(spmi_path):
        print(f"SPMI path '{spmi_path}' does not exist. Ensure the SuperPMI command ran successfully.")
        sys.exit(1)

    print(f"Copying contents of '{spmi_path}' (excluding 'mch') to '{output_folder_path}'...")
    try:
        os.makedirs(output_folder_path, exist_ok=True)
        for item in os.listdir(spmi_path):
            item_path = os.path.join(spmi_path, item)
            if os.path.isdir(item_path) and item.lower() == "mch":
                continue  # Skip the 'mch' folder
            shutil.move(item_path, os.path.join(output_folder_path, item))
        print(f"Copied contents to '{output_folder_path}' successfully.")
    except Exception as e:
        print(f"Failed to copy contents of '{spmi_path}' to '{output_folder_path}': {e}")
        sys.exit(1)

    # Delete the contents of spmi_path
    print(f"Deleting contents of '{spmi_path}'...")
    try:
        delete_directory_if_exists(spmi_path)
        print(f"Deleted contents of '{spmi_path}' successfully.")
    except Exception as e:
        print(f"Failed to delete contents of '{spmi_path}': {e}")
        sys.exit(1)

    return details_csv_path  # Return the dynamically created path

def create_visual_representation(*details_csv_paths):
    """
    Reads multiple diffAPX_details.csv files and creates separate graphs for:
    - Instruction Count Difference
    - % Instruction Count Difference
    - % Instruction Count Difference (Ignoring Zero diffs)
    """
    if not details_csv_paths:
        print("No CSV paths provided for visualization.")
        sys.exit(1)

    # Mapping of CSV prefixes to human-readable names
    label_mapping = {
        "16_eGPR_JitBypassApxCheck_1_EnableApxNDD_0_EnableApxConditionalChaining_0": "8 eGPR, NDD off, CCMP Off",
        "16_eGPR_JitBypassApxCheck_1_EnableApxNDD_1_EnableApxConditionalChaining_0": "8 eGPR, NDD on, CCMP Off",
        "16_eGPR_JitBypassApxCheck_1_EnableApxNDD_0_EnableApxConditionalChaining_1": "8 eGPR, NDD off, CCMP On",
        "16_eGPR_JitBypassApxCheck_1_EnableApxNDD_1_EnableApxConditionalChaining_1": "8 eGPR, NDD on, CCMP On",
        "future_branch_JitBypassApxCheck_1_EnableApxNDD_0_EnableApxConditionalChaining_0": "16 eGPR, NDD off, CCMP Off"
    }

    data_frames = []
    labels = []

    # Read and process each CSV file
    for csv_path in details_csv_paths:
        if not os.path.exists(csv_path):
            print(f"File '{csv_path}' does not exist. Ensure the file is generated correctly.")
            sys.exit(1)

        print(f"Reading diff details from '{csv_path}'...")
        try:
            # Read the CSV file
            data = pd.read_csv(csv_path)

            # Check if required columns exist
            required_columns = [
                'Collection',
                'Instruction Count Difference',
                '% Instruction Count Difference',
                '% Instruction Count Difference (Ignoring Zero diffs)'
            ]
            for column in required_columns:
                if column not in data.columns:
                    print(f"Required column '{column}' is missing in '{csv_path}'.")
                    sys.exit(1)

            # Remove '.mch' and '.windows' from the Collection column
            data['Collection'] = data['Collection'].str.replace('.mch', '', regex=False)
            data['Collection'] = data['Collection'].str.replace(r'\.windows.*', '', regex=True)

            # Add the data and label for comparison
            csv_name = os.path.splitext(os.path.basename(csv_path))[0]
            human_readable_label = label_mapping.get(csv_name, csv_name)  # Use mapping or fallback to the original name
            data_frames.append(data)
            labels.append(human_readable_label)

        except Exception as e:
            print(f"Failed to read or process '{csv_path}': {e}")
            sys.exit(1)

    # Merge all data frames on the 'Collection' column
    merged_data = data_frames[0]
    for i, df in enumerate(data_frames[1:], start=1):
        merged_data = pd.merge(
            merged_data,
            df,
            on='Collection',
            suffixes=('', f'_{i}')
        )

    # Define the columns to plot
    columns_to_plot = [
        'Instruction Count Difference',
        '% Instruction Count Difference',
        '% Instruction Count Difference (Ignoring Zero diffs)'
    ]

    # Add explanations for each graph
    explanations = {
        'Instruction Count Difference': r"$\bf{Instruction\ Count\ Difference}$ = $\bf{(Diff\ Instr\ Count\ -\ Base\ Instr\ Count)}$",
        '% Instruction Count Difference': r"$\bf{\% Instruction\ Count\ Difference}$ = $\bf{\frac{(Diff\ Instr\ Count\ -\ Base\ Instr\ Count)\ \times\ 100}{Base\ Instr\ Count}}$",
        '% Instruction Count Difference (Ignoring Zero diffs)': r"$\bf{\% Instruction\ Count\ Difference\ (Ignoring\ Zero\ Diffs)}$ = $\bf{\frac{(Diff\ Instr\ Count\ -\ Base\ Instr\ Count)\ \times\ 100}{Base\ Instr\ Count}}$ only for methods with diff"
    }

    # Create a graph for each column
    for column in columns_to_plot:
        print(f"Creating graph for column: {column}")
        plt.figure(figsize=(16, 10))

        # Plot each dataset
        x = range(len(merged_data['Collection']))
        width = 0.2  # Bar width
        gap = 0.5  # Gap between collections
        for i, label in enumerate(labels):
            column_name = column if i == 0 else f"{column}_{i}"
            bar_positions = [pos + (i * width) + (gap * pos) for pos in x]
            bar_values = merged_data[column_name]
            plt.bar(
                bar_positions,
                bar_values,
                width=width,
                label=label
            )

            # Add values above the bars
            for pos, value in zip(bar_positions, bar_values):
                plt.text(
                    pos, 
                    value + (0.02 * (value) if value != 0 else 0.1),  # Position slightly above the bar
                    f"{value:.2f}", 
                    ha='center', 
                    va='bottom', 
                    fontsize=8
                )

        # Configure the graph
        plt.xlabel("Collection")
        plt.ylabel(column)
        plt.title(
            f"{column}",
            fontweight="bold",  # Make the header bold
            fontsize=16         # Use a larger font size for the header
        )
        plt.xticks(
            [pos + (width * (len(labels) - 1) / 2) + (gap * pos) for pos in x],
            merged_data['Collection'],
            rotation=45,
            fontsize=10
        )
        plt.legend()
        plt.tight_layout()

        # Add explanation text to the graph
        explanation = explanations.get(column, "")
        plt.figtext(0.5, -0.05, explanation, wrap=True, horizontalalignment='center', fontsize=10)

        # Invert the y-axis to flip the graph
        plt.gca().invert_yaxis()

        # Save the graph
        graph_path = os.path.join(os.path.dirname(details_csv_paths[0]), f"{column.replace(' ', '_').lower()}_comparison.png")
        plt.savefig(graph_path, bbox_inches="tight")
        print(f"Graph for column '{column}' saved at '{graph_path}'.")

        # Show the graph
        # plt.show()

if __name__ == "__main__":
    print("Starting the script...")

    # Create a new folder 'runResults' parallel to the 'runtime' repository
    run_results_path = os.path.abspath(os.path.join(DIR_NAME, "..", "runResults"))
    if os.path.exists(run_results_path):
        print(f"'runResults' folder already exists at: {run_results_path}. Deleting its contents...")
        try:
            # Delete all contents of the folder
            for item in os.listdir(run_results_path):
                item_path = os.path.join(run_results_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            print(f"All contents of 'runResults' folder deleted successfully.")
        except Exception as e:
            print(f"Failed to delete contents of 'runResults' folder: {e}")
            sys.exit(1)
    else:
        print(f"'runResults' folder does not exist. Creating it at: {run_results_path}")
        try:
            os.makedirs(run_results_path)
            print(f"'runResults' folder created successfully.")
        except Exception as e:
            print(f"Failed to create 'runResults' folder: {e}")
            sys.exit(1)

    # Add jitutils\bin to the PATH environment variable
    jitutils_bin_path = os.path.abspath(os.path.join(JITUTILS_DIR_NAME, "bin"))
    os.environ["PATH"] += os.pathsep + jitutils_bin_path
    print(f"Added '{jitutils_bin_path}' to PATH.")

    # Get the absolute path to the repository directory
    repo_root = os.path.abspath(DIR_NAME)
    print(f"Repository root path: {repo_root}")

    # Check if the repository directory already exists
    if os.path.exists(repo_root):
        print(f"Directory '{repo_root}' already exists. Skipping cloning step.")
    else:
        # Clone the repository
        clone_repo(REPO_URL, DIR_NAME)

    # Define branches to test
    branches = ["16_eGPR"]  # Add your branch names here

    # Define diff_jit_options for each branch
    diff_jit_options_16_eGPR = [
        ["JitBypassApxCheck=1", "EnableApxNDD=0", "EnableApxConditionalChaining=0"],
        ["JitBypassApxCheck=1", "EnableApxNDD=1", "EnableApxConditionalChaining=0"],
        ["JitBypassApxCheck=1", "EnableApxNDD=0", "EnableApxConditionalChaining=1"],
        ["JitBypassApxCheck=1", "EnableApxNDD=1", "EnableApxConditionalChaining=1"]
    ]
    diff_jit_options_future_branch = [
        ["JitBypassApxCheck=1", "EnableApxNDD=0", "EnableApxConditionalChaining=0"]
    ]
    base_jit_options = [
        ["JitBypassApxCheck=0", "EnableApxNDD=0", "EnableApxConditionalChaining=0"]
    ]

    # Collect all CSV paths for both branches
    all_details_csv_paths = []

    # Iterate over branches and run superpmi for each branch
    for branch in branches:
        print(f"Processing branch: {branch}")
        checkout_branch(branch, cwd=repo_root)

        # Run the build commands after checking out the branch
        build_cmd_path = os.path.join(repo_root, "build.cmd")
        tests_build_cmd_path = os.path.join(repo_root, "src", "tests", "build.cmd")
        run_command([build_cmd_path, "clr+libs", "-rc", "checked", "-lc", "Release"], cwd=repo_root)
        run_command([tests_build_cmd_path, "x64", "Checked", "generatelayoutonly"], cwd=repo_root)

        # Copy Core_Root to the results folder and rename it to 'base' only for the '16_eGPR' branch
        if branch == "16_eGPR":
            copy_core_root(repo_root, run_results_path, "base")

        # Copy Core_Root to the results folder and rename it to the branch name
        copy_core_root(repo_root, run_results_path, branch)

        diff_coreroot_path = os.path.join(run_results_path, branch)

        # Run superpmi for the specific configurations
        if branch == "16_eGPR":
            for diff_jit_options in diff_jit_options_16_eGPR:
                csv_prefix = f"{branch}"
                details_csv_path = run_superpmi(
                    repo_root,
                    run_results_path,
                    csv_prefix,
                    diff_coreroot_path,
                    diff_jit_options,
                    base_jit_options
                )
                all_details_csv_paths.append(details_csv_path)
        elif branch == "future_branch":
            for diff_jit_options in diff_jit_options_future_branch:
                csv_prefix = f"{branch}"
                details_csv_path = run_superpmi(
                    repo_root,
                    run_results_path,
                    csv_prefix,
                    diff_coreroot_path,
                    diff_jit_options,
                    base_jit_options
                )
                all_details_csv_paths.append(details_csv_path)

    # Create a visual representation for all cases across both branches
    create_visual_representation(*all_details_csv_paths)

    print("Script completed successfully.")