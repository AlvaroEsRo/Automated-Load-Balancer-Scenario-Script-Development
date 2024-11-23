import sys
import json
import logging
from lib_vm import VM, NET
import subprocess
import os
import shutil

# Logger initialization
def init_log(debug=False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger("manage-p2")

# Read configuration from JSON file
def read_config(file_path):
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        number_of_servers = config.get("number_of_servers", 0)
        debug = config.get("debug", False)
        if not (1 <= number_of_servers <= 5):
            raise ValueError("The number of servers must be between 1 and 5.")
        return number_of_servers, debug
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)

# Monitor the status of the machines
def monitor(machines):
    """
    Monitors the status of all virtual machines in the scenario.
    """
    print("Status of virtual machines:")
    print("-" * 40)
    for machine in machines:
        try:
            # Use a system command to check the status of the virtual machine
            result = subprocess.run(
                ["sudo", "virsh", "domstate", machine],  # Command to get the machine's status
                check=True,
                text=True,
                capture_output=True
            )
            state = result.stdout.strip()  # Machine state (e.g., running, shut off)
            print(f"{machine}: {state}")
        except subprocess.CalledProcessError as e:
            print(f"{machine}: Error retrieving status - {e.stderr.strip()}")
        except FileNotFoundError:
            print(f"{machine}: Error - 'virsh' command not found. Ensure it is installed.")
    print("-" * 40)

# Create virtual machines
def create(machines, nets):
    template_image = "cdps-vm-base-pc1.qcow2"

    # Iterate over the VM array
    for machine in machines:
        # Create an instance of the VM class to create the machines
        vm = VM(machine)
        vm.create_vm(template_image, machine)
    for net in nets:
        lan = NET(net)
        lan.create_net()
        print(f"Network {net} created")
    for machine in machines:
        vm = VM(machine)
        vm.define_vm()


def start(machines, machine_name=None):
    """
    Starts all machines or a specific one if machine_name is provided.
    """
    if machine_name:
        if machine_name in machines:
            vm = VM(machine_name)
            vm.start_vm(machine_name)
            print(f"Machine {machine_name} started and console displayed")
        else:
            print(f"Error: Machine {machine_name} does not exist.")
    else:
        for machine in machines:
            vm = VM(machine)
            vm.start_vm(machine)
        print("All machines started and consoles displayed")


def stop(machines, machine_name=None): 
    """
    Stops all machines or a specific one if machine_name is provided.
    """
    if machine_name:
        if machine_name in machines:
            vm = VM(machine_name)
            vm.stop_vm()
            print(f"Machine {machine_name} stopped")
        else:
            print(f"Error: Machine {machine_name} does not exist.")
    else:
        for machine in machines:
            vm = VM(machine)
            vm.stop_vm()
        print("All machines stopped")

def destroy(machines, nets):
    for machine in machines:
        vm = VM(machine)
        vm.destroy_vm()
    for net in nets:
        lan = NET(net)
        lan.destroy_net()
        print(f"Network {net} removed")

    pycache_path = os.path.abspath("__pycache__")  

    if os.path.exists(pycache_path):
        if os.path.isdir(pycache_path):  # Verify if it is a directory
            print(f"Deleting directory and its contents: {pycache_path}")
            shutil.rmtree(pycache_path)  # Delete the directory and its contents
            print("Directory successfully removed.")
        else:
            print(f"{pycache_path} is not a directory.")
    else:
        print(f"Directory not found: {pycache_path}")
    subprocess.call(["pkill", "xterm"])
    print("Consoles closed successfully.")
    print("Machines destroyed")

# Main function
def main():
    try:
        result = subprocess.run(
        ["/lab/cnvr/bin/prepare-vnx-debian"],  # Command necessary to start everything
        check=True,  
        text=True,   
        capture_output=True  
    )
        print("Command executed: prepare-vnx-debian:")
        print(result.stdout)  
    except subprocess.CalledProcessError as e:
        print(f"The command failed with exit code {e.returncode}:")
        print(e.stderr)  # Display the captured error
    except FileNotFoundError:
        print("Command not found. Ensure the path is correct.")

    if len(sys.argv) < 2:
        print("Usage: manage-p2.py <command>")
        sys.exit(1)

    order = sys.argv[1].lower()
    config_file = "manage-p2.json"

    # Read configuration and set up logging
    number_of_servers, debug = read_config(config_file)
    logger = init_log(debug)

    machines = ["lb"] + ["c1"] + [f"s{i}" for i in range(1, number_of_servers + 1)] 

    # Array of NETs
    nets = ["LAN1"] + ["LAN2"]
    

    # Process the command
    if order == "create":
        create(machines, nets)
        logger.info("Machines and bridges created successfully")
    elif order == "start":
        # Detect if there is an additional argument for a specific machine
        if len(sys.argv) > 2:
            machine_name = sys.argv[2]
            start(machines, machine_name)
        else:
            start(machines)
            logger.info("Machines started successfully")
        
    elif order == "stop":
        # Detect if there is an additional argument for a specific machine
        if len(sys.argv) > 2:
            machine_name = sys.argv[2]
            stop(machines, machine_name)
        else:
            stop(machines)
            logger.info("Machines stopped successfully")

    elif order == "destroy":
        destroy(machines, nets)
        logger.info("Machines destroyed successfully")

    elif order == "monitor":
        monitor(machines)
        logger.info("Monitoring executed successfully")
        
    else:
        logger.error(f"Unknown command: {order}")
        sys.exit(1)

if __name__ == "__main__":
    main()
