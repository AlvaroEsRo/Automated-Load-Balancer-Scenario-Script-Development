import logging
from lxml import etree
import subprocess
import os

log = logging.getLogger('manage-p2')

# GLOBAL VARIABLES

# Array containing all possible virtual machines to create with their IP addresses and gateways
ip =[
    {"vm_name": "lb", "ip_address" : "10.1.1.1", "gateaway" : "null"},
    {"vm_name": "c1", "ip_address" : "10.1.1.2", "gateaway" : "10.1.1.1"},
    {"vm_name": "s1", "ip_address" : "10.1.2.11", "gateaway" : "10.1.2.1"},
    {"vm_name": "s2", "ip_address" : "10.1.2.12", "gateaway" : "10.1.2.1"},
    {"vm_name": "s3", "ip_address" : "10.1.2.13", "gateaway" : "10.1.2.1"},
    {"vm_name": "s4", "ip_address" : "10.1.2.14", "gateaway" : "10.1.2.1"},
    {"vm_name": "s5", "ip_address" : "10.1.2.15", "gateaway" : "10.1.2.1"}
]

# HELPER METHODS

# lb needs a second interface because it is connected to two LANs; this method adds that second interface to lb.xml
def add_second_interface_for_lb(root):
    # Locate the first interface node
    first_interface = root.find(".//devices/interface")

    # Clone the first interface node
    second_interface = etree.Element("interface", type="bridge")
    second_source = etree.SubElement(second_interface, "source")

    # Configure LAN2 bridge
    second_source.set("bridge", "LAN2")  
    model_element = etree.SubElement(second_interface, "model")
    model_element.set("type", "virtio")

    # Create and add the <virtualport type="openvswitch"/> node in the second interface
    virtualport_element = etree.SubElement(second_interface, "virtualport")
    virtualport_element.set("type", "openvswitch")

    # Add the new interface to the XML
    root.find(".//devices").append(second_interface)

# Method to create the network configuration file for each machine
def create_vm_config(vm_name, ip_address, gateway, netmask="255.255.255.0"):
    # Create a temporary directory to store configuration files
    temp_dir = "/tmp/vm_configs"
    os.makedirs(temp_dir, exist_ok=True)

    # Paths for configuration files
    hostname_path = os.path.join(temp_dir, "hostname")
    interfaces_path = os.path.join(temp_dir, "interfaces")

    # Write the /etc/hostname file
    with open(hostname_path, "w") as hostname_file:
        hostname_file.write(vm_name)
    if(vm_name == "lb"):
        with open(interfaces_path, "w") as interfaces_file:
            interfaces_file.write(f"""auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static
    address {ip_address}
    netmask {netmask}
auto eth1
iface eth1 inet static
    address {"10.1.2.1"}
    netmask {netmask}
""")

    else:
    # Write the /etc/network/interfaces file
        with open(interfaces_path, "w") as interfaces_file:
            interfaces_file.write(f"""auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static
    address {ip_address}
    netmask {netmask}
    gateway {gateway}
""")

    print(f"Configuration files created for {vm_name}:")
    print(f" - {hostname_path}")
    print(f" - {interfaces_path}")
    return hostname_path, interfaces_path

# Method to copy the configuration file to each machine
def copy_config_to_vm(vm_name, hostname_path, interfaces_path):
    try:
        # Copy the "hostname" file
        subprocess.call(["sudo", "virt-copy-in", "-a",f"{vm_name}.qcow2", hostname_path, "/etc"])
        print(f"Hostname file copied to {vm_name}")

        # Copy the "interfaces" file
        subprocess.call(["sudo", "virt-copy-in", "-a", f"{vm_name}.qcow2", interfaces_path, "/etc/network"])
        print(f"Interfaces file copied to {vm_name}")
    except Exception as e:
        print(f"Error copying files to {vm_name}: {e}")

# Method to change the hosts file of each VM
def changehostsname(name):
    try:
        subprocess.call([
        "sudo", "virt-edit", 
        "-a", f"{name}.qcow2", 
        "/etc/hosts", 
        "-e", f"s/127.0.1.1.*/127.0.1.1 {name}/"
    ])
        print(f"/etc/hosts updated on virtual machine {name}.")
    except Exception as e:
        print(f"Error executing the command: {e}")

# Execute the command to configure lb as a router by changing the /etc/sysctl.conf file
def configlbtorouter(name):
    try:
        subprocess.call([
        "sudo", "virt-edit", 
        "-a", f"{name}.qcow2", 
        "/etc/sysctl.conf", 
        "-e", "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/"
    ])
        print(f"/etc/sysctl.conf updated on virtual machine {name}.")
    except Exception as e:
        print(f"Error executing the command: {e}")

# Launch the consoles of virtual machines
def startconsole(name):
    subprocess.call(f"sudo virsh start {name}", shell=True)
    print(f"Virtual machine {name} has started.")

    # Command to open the console of the virtual machine in a new terminal
    subprocess.call(f"xterm -e 'sudo virsh console {name}' &", shell=True)
    print(f"Console of {name} opened in a new terminal.")

# VM Class
class VM:
    # Initialize the VM
    def __init__(self, name):
        self.name = name
        log.debug(f'init VM {self.name}')

    # Create the VMs
    def create_vm(self, image, machine):
        log.debug(f"create_vm {self.name} (image: {image})")
        try:
            # Clone the base image
            subprocess.call(["qemu-img", "create", "-F", "qcow2", "-f", "qcow2", "-b", image, f"{self.name}.qcow2"])
            log.debug(f"Base image cloned: {self.name}.qcow2")

            # Create XML file
            tree = etree.parse('plantilla-vm-pc1.xml')
            root = tree.getroot()

            root.find("./name").text = self.name

            qcow_path = os.path.abspath(f"{self.name}.qcow2")
            root.find(".//devices/disk/source").set("file", qcow_path)

            print("Absolute path: ", qcow_path)

            # Configure interfaces
            if machine == "lb":
                # First interface connected to LAN1
                interface_element = root.find(".//devices/interface/source")
                interface_element.set("bridge", "LAN1")
                interface = root.find(".//devices/interface")
                # Create and add the <virtualport type="openvswitch"/> node
                virtualport_element = etree.SubElement(interface, "virtualport")
                virtualport_element.set("type", "openvswitch")

                # Add second interface connected to LAN2
                add_second_interface_for_lb(root)
            elif machine == "c1":
                # First interface connected to LAN1
                interface_element = root.find(".//devices/interface/source")
                interface = root.find(".//devices/interface")
                interface_element.set("bridge", "LAN1")
                # Create and add the <virtualport type="openvswitch"/> node
                virtualport_element = etree.SubElement(interface, "virtualport")
                virtualport_element.set("type", "openvswitch")

            print("VM created")

            # Save XML file
            tree.write(f"{self.name}.xml", pretty_print=True, xml_declaration=True, encoding="UTF-8")
            log.debug(f"Generated XML file: {self.name}.xml")
        except Exception as e:
            log.error(f"Error creating VM {self.name}: {e}")
            raise

# Define virtual machines
def define_vm(self):
    try:
        # Check if the VM already exists
        result = subprocess.run(["sudo", "virsh", "list", "--all"], capture_output=True, text=True)
        
        # Stop and undefine the VM if it exists
        if self.name in result.stdout:
            subprocess.call(["sudo", "virsh", "destroy", self.name])
            subprocess.call(["sudo", "virsh", "undefine", self.name])
            print(f"Machine {self.name} undefined and destroyed.")

        # Define the machine again
        subprocess.call(["sudo", "virsh", "define", f"{self.name}.xml"])

    except Exception as e:
        log.error(f"Error defining VM {self.name}: {e}")
        

# Start VMs
def start_vm(self, machine):
    # Iterate through the array with each virtual machine and its IP, calling the method to configure the networks of each machine with its IP and gateway
    for i in ip:
        name = i['vm_name'] 
        # Ensure only the number of machines indicated in manage-p2.json are started, not all included in the IP array
        if(name == machine):
            hostname_path, interface_path = create_vm_config(name, i['ip_address'], i['gateaway']) # Method to create the network configuration file for each machine
            copy_config_to_vm(name, hostname_path, interface_path) # Method to copy the config file to each machine
            changehostsname(name) # Execute the command to change the hosts file of each VM
            if(name == 'lb'):
                configlbtorouter(name)
            startconsole(name)
        

# Stop VMs
def stop_vm(self):
    try:
        # Command to shut down the virtual machine
        result = subprocess.call(["sudo", "virsh", "shutdown", self.name])
        if result == 0:
            print(f"The virtual machine '{self.name}' is shutting down correctly.")
        else:
            print(f"Error trying to shut down the virtual machine '{self.name}'. Verify if it exists or is active.")
    except Exception as e:
        print(f"Exception while trying to shut down the virtual machine '{self.name}': {e}")


# Destroy VMs
def destroy_vm(self):
    try:
        # Attempt to stop the VM if it's running
        print(f"Attempting to destroy the VM '{self.name}'...")
        result = subprocess.call(["sudo", "virsh", "destroy", self.name])
        if result == 0:
            print(f"Virtual machine '{self.name}' destroyed successfully.")
        else:
            print(f"Could not destroy the virtual machine '{self.name}'. Verify if it is active.")
    
        # Undefine the VM
        print(f"Undefining the VM '{self.name}'...")
        subprocess.call(["sudo", "virsh", "undefine", self.name])

        # Paths of the files to delete
        xml_path = os.path.abspath(f"{self.name}.xml")
        qcow2_path = os.path.abspath(f"{self.name}.qcow2")
        

        # Delete the XML file
        if os.path.exists(xml_path):
            print(f"Deleting XML file: {xml_path}")
            os.remove(xml_path)
        else:
            print(f"XML file not found: {xml_path}")

        # Delete the qcow2 file
        if os.path.exists(qcow2_path):
            print(f"Deleting image file: {qcow2_path}")
            os.remove(qcow2_path)
        else:
            print(f"Image file not found: {qcow2_path}")

        log.info(f"VM '{self.name}' fully deleted (destroyed, undefined, and files removed).")

    except Exception as e:
        log.error(f"Error destroying and cleaning up VM '{self.name}': {e}")
        print(f"Error destroying and cleaning up VM '{self.name}': {e}")


class NET:
    # Initialize the NET class
    def __init__(self, name):
        self.name = name
        log.debug(f'init net {self.name}')

    # Create LAN networks
    def create_net(self):
        log.debug(f'create_net {self.name}')
        subprocess.call(["/lab/cnvr/bin/prepare-vnx-debian"])
        subprocess.call(['sudo', 'ovs-vsctl', 'add-br', self.name])

    # Destroy LAN networks
    def destroy_net(self):
        log.debug(f'destroy_net {self.name}')
        subprocess.call(['sudo', 'ovs-vsctl', 'del-br', self.name])
        

