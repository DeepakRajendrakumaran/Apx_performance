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

def run_superpmi(repo_root, destination_path):
    """Run the superpmi.py command."""
    # Delete the artifacts\spmi directory if it exists
    spmi_path = os.path.join(repo_root, "artifacts", "spmi")
    delete_directory_if_exists(spmi_path)

    details_csv_path = os.path.join(destination_path, "diffAPX_details.csv")
    base_jit_path = os.path.join(destination_path, "base", "clrjit.dll")
    diff_jit_path = os.path.join(destination_path, "diffAPX", "clrjit.dll")
    superpmi_script = os.path.join(repo_root, "src", "coreclr", "scripts", "superpmi.py")

    command = [
        "python", superpmi_script, "asmdiffs",
        "-details", details_csv_path,
        "-base_jit_path", base_jit_path,
        "-diff_jit_path", diff_jit_path,
        "-diff_jit_option", "JitBypassApxCheck=1",
        "-filter", "libraries_tests.run"
    ]

    print(f"Running SuperPMI command: {' '.join(command)}")
    run_command(command, cwd=repo_root)

def create_visual_representation(diff_csv_path):
    """
    Reads the diffAPX_details.csv file and creates a graph comparing 'Instruction Count Difference'.
    """
    if not os.path.exists(diff_csv_path):
        print(f"File '{diff_csv_path}' does not exist. Ensure the file is generated correctly.")
        sys.exit(1)

    print(f"Reading diff details from '{diff_csv_path}'...")
    try:
        # Read the CSV file
        data = pd.read_csv(diff_csv_path)
        print(f"Successfully read data from '{diff_csv_path}'.")

        # Check if required columns exist
        if 'Collection' not in data.columns:
            print("Required column ('Name') missing in the CSV file.")
            sys.exit(1)

        if 'Instruction Count Difference' not in data.columns:
            print("Required columns ('Instruction Count Difference') is missing in the CSV file.")
            sys.exit(1)

        # Extract data for plotting
        labels = data['Collection'].str.split('.').str[0]  # Truncate labels until the first period
        instruction_count_diff = data['Instruction Count Difference']

        print("Creating the bar graph...")
        plt.figure(figsize=(12, 8))
        plt.bar(labels, instruction_count_diff, color="skyblue")
        plt.xlabel("Collection")
        plt.ylabel("Instruction Count Difference")
        plt.title("Instruction Count Difference")
        plt.xticks(rotation=45, fontsize=10)
        plt.tight_layout()

        # Save the graph as an image
        graph_path = os.path.join(os.path.dirname(diff_csv_path), "instruction_count_difference_graph.png")
        plt.savefig(graph_path)
        print(f"Graph saved at '{graph_path}'.")

        # Show the graph
        print("Displaying the graph...")
        plt.show()

    except Exception as e:
        print(f"Failed to create visual representation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting the script...")

    # Create a new folder 'runResults' parallel to the 'runtime' repository
    run_results_path = os.path.abspath(os.path.join(DIR_NAME, "..", "runResults"))
    
    # Path to the diff_short_summary.md file
    diff_summary_path = os.path.join(run_results_path, "diffAPX_details.csv")

    # Create a visual representation of the diff summary
    create_visual_representation(diff_summary_path)

    print("Script completed successfully.")