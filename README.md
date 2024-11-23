# **Virtual Machine Manager: `manage-p2.py` and `lib_vm.py`**

---

## **Authors**
- **Elena Lopez de la Cruz**
- **Alvaro Estevez Rodriguez**

## **Requirements**

- **Python 3.x**: The script is designed to work with Python 3.x.
- **Python Libraries**: The following libraries are required:
    - `lxml`: For XML manipulation. You can install it by running:
      ```bash
      pip install lxml
      ```
    - `subprocess`: Used to execute system commands.

- **System Tools**: The following tools must be installed on the machine:
    - `qemu-img`, `virsh`, `ovs-vsctl`: For managing virtual machines and networks.
    - `virt-copy-in`, `virt-edit`: Tools for modifying and copying files inside VMs.

---

## **Description**

### **`manage-p2.py`**
This is the main script that manages operations on virtual machines (VMs) and networks. It supports the following actions:

- **create**: Creates the virtual machines and networks.
- **start**: Starts the virtual machines and opens their consoles in new terminals.
- **stop**: Shuts down the virtual machines.
- **destroy**: Deletes the virtual machines and networks.
- **monitor**: Displays the current status of the virtual machines.

### **`lib_vm.py`**
This file contains the `VM` and `NET` classes, which provide the functions needed to configure, create, manipulate, and destroy virtual machines and networks.

- **Classes**:
    - **`VM`**: Class responsible for managing virtual machines. Includes methods for creating, defining, starting, stopping, and destroying VMs.
    - **`NET`**: Class for managing virtual networks, including creating and destroying virtual bridges.

- **Helper Methods**:
    - **`create_vm_config`**: Creates the network configuration files for virtual machines.
    - **`copy_config_to_vm`**: Copies the configuration files to the virtual machines.
    - **`startconsole`**: Opens a virtual machine console in a new terminal.
    - **`configlbtorouter`**: Configures the `lb` machine as a router, enabling IP forwarding.

---

## **Usage**

### **1. Initial Configuration**
- The `manage-p2.json` file must exist in the same directory where the script is executed. This file contains the configuration for the virtual machines (number of servers and whether to enable debug mode).

### **2. Available Commands**

Run the script with one of the following commands:

#### **`create`**
Creates the virtual machines and networks defined in the configuration.

```bash
python manage-p2.py create
```

#### **`start`**
Starts the virtual machines. If you want to start a specific machine, provide its name.

```bash
python manage-p2.py start
python manage-p2.py start <machine_name>
```
#### **`stop`**
Stops the virtual machines. If you want to stop a specific machine, provide its name.

```bash
python manage-p2.py stop
python manage-p2.py stop <machine_name>
```

#### **`destroy`**
Destroys the virtual machines and networks.

```bash
python manage-p2.py destroy
```
#### **`monitor`**
Displays the current status of the virtual machines.

```bash
python manage-p2.py monitor
```

### **3. Detailed Functions**

#### **`lib_vm.py`**

##### **`VM class`**

- **`__init__(self, name)`**: Initializes a new virtual machine with the given name.

- **`create_vm(self, image, machine)`**: Creates a virtual machine based on a template image.

- **`define_vm(self)`**: Defines the VM in virsh after creation, removing any previous instance if it exists.

- **`start_vm(self, machine)`**: Starts the virtual machine, sets up the network, and launches the console.

- **`stop_vm(self)`**: Stops the virtual machine.

- **`destroy_vm(self)`**: Deletes the virtual machine and its related files.

##### **`NET class`**

- **`create_net(self)`**: Creates a virtual network using ovs-vsctl and configures it.

- **`destroy_net(self)`**: Destroys the virtual network associated with the network name.


### **4. OPTIONAL Detailed Features**

We have implemented two optional features that have been explained earlier:

- **`Comando monitor`**: Displays the current status of the VMs on the screen.
- **`Arraque y parada de una MV`**: Allows the user to start or stop a specific VM by specifying its name in the command.

### **5. Configuration Files**

#### **`manage-p2.json`**
This file must contain at least the following parameters:

- **`number_of_servers`**: The number of servers to manage (from 1 to 5).
- **`debug`**: Enables logging mode (if true, debug messages are activated).

