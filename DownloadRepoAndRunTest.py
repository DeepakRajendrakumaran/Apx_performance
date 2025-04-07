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

def run_superpmi(repo_root, destination_path, csv_prefix, diff_jit_options):
    """Run the superpmi.py command with specified csv_prefix and diff_jit_options."""
    # Delete the artifacts\spmi directory if it exists
    spmi_path = os.path.join(repo_root, "artifacts", "spmi")
    delete_directory_if_exists(spmi_path)

    # Create a unique name for the details CSV file based on csv_prefix and diff_jit_options
    options_suffix = "_".join(option.replace("=", "_") for option in diff_jit_options)
    details_csv_path = os.path.join(destination_path, f"{csv_prefix}_{options_suffix}.csv")

    base_jit_path = os.path.join(destination_path, "base", "clrjit.dll")
    diff_jit_path = os.path.join(destination_path, "diffAPX", "clrjit.dll")
    superpmi_script = os.path.join(repo_root, "src", "coreclr", "scripts", "superpmi.py")

    # Build the command
    command = [
        "python", superpmi_script, "asmdiffs",
        "-details", details_csv_path,
        "-base_jit_path", base_jit_path,
        "-diff_jit_path", diff_jit_path,
    ]

    # Add all diff_jit_options to the command
    for option in diff_jit_options:
        command.extend(["-diff_jit_option", option])

    # Add the filter
    # command.extend(["-filter", "libraries_tests.run"])

    print(f"Running SuperPMI command: {' '.join(command)}")
    run_command(command, cwd=repo_root)

    return details_csv_path  # Return the dynamically created path

def create_visual_representation(*details_csv_paths):
    """
    Reads multiple diffAPX_details.csv files and creates a comparative graph of '% Instruction Count Difference'.
    """
    if not details_csv_paths:
        print("No CSV paths provided for visualization.")
        sys.exit(1)

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
            if 'Collection' not in data.columns or '% Instruction Count Difference' not in data.columns:
                print(f"Required columns ('Collection', '% Instruction Count Difference') are missing in '{csv_path}'.")
                sys.exit(1)

            # Add the data and label for comparison
            data_frames.append(data[['Collection', '% Instruction Count Difference']])
            labels.append(os.path.splitext(os.path.basename(csv_path))[0])  # Use the file name (without extension) as the label

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

    # Plot the comparative graph
    print("Creating the comparative bar graph...")
    plt.figure(figsize=(16, 10))

    # Plot each dataset
    x = range(len(merged_data['Collection']))
    width = 0.2  # Bar width
    for i, label in enumerate(labels):
        column_name = '% Instruction Count Difference' if i == 0 else f'% Instruction Count Difference_{i}'
        plt.bar(
            [pos + (i * width) for pos in x],
            merged_data[column_name],
            width=width,
            label=label
        )

    # Configure the graph
    plt.xlabel("Collection")
    plt.ylabel("% Instruction Count Difference")
    plt.title("Comparison of % Instruction Count Difference Across Collections")
    plt.xticks([pos + (width * (len(labels) - 1) / 2) for pos in x], merged_data['Collection'].str.split('.').str[0], rotation=45, fontsize=10)
    plt.legend()
    plt.tight_layout()

    # Save the graph
    graph_path = os.path.join(os.path.dirname(details_csv_paths[0]), "comparison_instruction_count_difference.png")
    plt.savefig(graph_path)
    print(f"Graph saved at '{graph_path}'.")

    # Show the graph
    print("Displaying the graph...")
    plt.show()

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

    # Switch to the main branch
    switch_to_main(repo_root)

    # Construct the full paths to the build scripts
    build_cmd_path = os.path.join(repo_root, "build.cmd")
    tests_build_cmd_path = os.path.join(repo_root, "src", "tests", "build.cmd")
    print(f"Build script path: {build_cmd_path}")
    print(f"Tests build script path: {tests_build_cmd_path}")


    # Check out the specified remote branch
    checkout_branch(BRANCH_NAME, cwd=repo_root)

    # Run the build commands again after checking out APX_icount
    run_command([build_cmd_path, "clr+libs", "-rc", "checked", "-lc", "Release"], cwd=repo_root)
    run_command([tests_build_cmd_path, "x64", "Checked", "generatelayoutonly"], cwd=repo_root)

    # Copy Core_Root to the results folder and rename it to 'base'
    copy_core_root(repo_root, run_results_path, "base")

    # Copy Core_Root to the results folder and rename it to 'diffAPX'
    copy_core_root(repo_root, run_results_path, "diffAPX")

    # Set up jitutils and run bootstrap.cmd
    setup_jitutils()

    # Run the SuperPMI command with 16eGPR as csv_prefix
    diff_jit_options1 = ["JitBypassApxCheck=1", "EnableApxNDD=0", "EnableApxConditionalChaining=0"]
    details_csv_path1 = run_superpmi(
        repo_root,
        run_results_path,
        "16eGPR",  # Updated csv_prefix
        diff_jit_options1
    )
    diff_jit_options2 = ["JitBypassApxCheck=1", "EnableApxNDD=1", "EnableApxConditionalChaining=0"]
    details_csv_path2 = run_superpmi(
        repo_root,
        run_results_path,
        "16eGPR",  # Updated csv_prefix
        diff_jit_options2
    )
    diff_jit_options3 = ["JitBypassApxCheck=1", "EnableApxNDD=0", "EnableApxConditionalChaining=1"]
    details_csv_path3 = run_superpmi(
        repo_root,
        run_results_path,
        "16eGPR",  # Updated csv_prefix
        diff_jit_options3
    )

    diff_jit_options4 = ["JitBypassApxCheck=1", "EnableApxNDD=1", "EnableApxConditionalChaining=1"]
    details_csv_path4 = run_superpmi(
        repo_root,
        run_results_path,
        "16eGPR",  # Updated csv_prefix
        diff_jit_options4
    )

    # Create a visual representation of the results
    create_visual_representation(details_csv_path1, details_csv_path2, details_csv_path3, details_csv_path4)

    print("Script completed successfully.")