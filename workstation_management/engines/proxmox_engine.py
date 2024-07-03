from proxmoxer import ProxmoxAPI, ResourceException
from regex import search
from engine import Engine
import logging
import time
import os
import urllib3

if os.environ.get('PROXMOX_VERIFY_SSL', 'True') == 'False':
    urllib3.disable_warnings()

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s:%(lineno)d] %(message)s', 
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_until_true(func, timeout=30, check_interval=1):
    while True:
        result = func()
        logger.info(result)
        if result:
            return
        time.sleep(check_interval)
        timeout -= check_interval
        if timeout <= 0:
            raise TimeoutError('Timeout reached')


class ProxmoxEngine(Engine):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs) 
        self.name = 'ProxmoxEngine'
        self.settings = {
            'host': os.environ.get('PROXMOX_HOST') or '127.0.0.1',
            'user': os.environ.get('PROXMOX_USER') or 'root@pam',
            'password': os.environ.get('PROXMOX_PASSWORD') or 'Qwerty123',
            'verify_ssl': os.environ.get('PROXMOX_VERIFY_SSL') or False,
            'primary_node': os.environ.get('PROXMOX_PRIMARY_NODE') or 'pve',
        }

        self.api = ProxmoxAPI(
            host=self.settings['host'],
            user=self.settings['user'],
            password=self.settings['password'],
            verify_ssl=self.settings['verify_ssl']
        )

        self.proxmox_templates = None
        self.vms = None
        self.highest_vmid = None

        self.reload_ids()
        self.reload_templates()
        self.reload_vms()

    def wait_for_agent_exec_result(self, vmid, pid, get_output=True):
        while True:
            response = self.api.nodes(self.settings['primary_node']).qemu(vmid).agent('exec-status').get(
                pid=pid)
            if response['exited'] == 1:
                return response['out-data'] if get_output else response
            time.sleep(1)

    def reload_ids(self):
        self.highest_vmid = 100
        for node in self.api.nodes.get(): 
            if node['node'] == self.settings['primary_node']:
                for vm in self.api.nodes(node['node']).qemu.get():
                    if vm['vmid'] > self.highest_vmid:
                        self.highest_vmid = vm['vmid']  

    def reload_vms(self):
        self.vms = self.get_all_vms()

    def reload_templates(self):
        self.proxmox_templates = self.get_all_proxmox_templates() 

    def get_id_for_new_vm(self) -> int:
        self.highest_vmid += 1
        return self.highest_vmid
    
    def check_if_template_exists(self, template_name: str) -> bool:
        return template_name in self.proxmox_templates

    def create_vm(self, template_name: str, vm_name: str) -> str:
        logger.info(f'Creating VM {vm_name} from template {template_name}')

        newid = self.get_id_for_new_vm()

        if not self.check_if_template_exists(template_name):
            return f'Template {template_name} does not exist'

        template_id = self.proxmox_templates[template_name]['vmid'] 
        response = self.api\
            .nodes(self.settings['primary_node'])\
            .qemu(template_id)\
            .clone.post(
                    newid=newid,
                    name=vm_name,
                )
        logger.info(response)
        while vm_name not in self.vms:
            self.reload_vms()
            time.sleep(1)
        return 'VM created'

    def is_vm_running(self, vm_name: str) -> bool:
        vmid = self.get_vm_id_by_name(vm_name)
        result = self.api.nodes(self.settings['primary_node']).qemu(vmid).status.current.get() 
        return result['status'] == 'running'
    
    def is_agent_running(self, vm_name: str) -> bool:
        vmid = self.get_vm_id_by_name(vm_name)
        try:
            self.api.nodes(self.settings['primary_node']).qemu(vmid).agent.exec.post(command=['whoami'])
        except ResourceException as e:
            return False
        else:
            return True
        
    def get_resource_usage(self) -> dict:
        response = self.api.nodes(self.settings['primary_node']).status.get()
        logger.info(f'Node resource usage: {response}')
        return response


    def delete_vm(self, vm_name: str) -> str:

        if vm_name not in self.vms:
            return 'VM does not exist'

        if self.is_vm_running(vm_name):
            self.stop_vm(vm_name)
            logger.info(f'Waiting for VM {vm_name} to stop')
            wait_until_true(lambda: not self.is_vm_running(vm_name))
            logger.info('VM stopped')

        vmid = self.get_vm_id_by_name(vm_name)
        response = self.api.nodes(self.settings['primary_node']).qemu(vmid).delete()
        logger.info(response)

        timeout = 10
        while vm_name in self.vms:
            self.reload_vms()
            time.sleep(1)
            timeout -= 1
            if timeout <= 0:
                return 'Timeout reached while waiting for VM to be deleted'

        return response
    
    def vm_exists(self, vm_name: str) -> bool:
        return vm_name in self.vms
    
    def template_exists(self, template_name: str) -> bool:
        return template_name in self.proxmox_templates
    
    def get_vm_id_by_name(self, vm_name: str) -> int:
        if not self.vm_exists(vm_name):
            raise ValueError(f'VM {vm_name} does not exist')
        return self.vms[vm_name]['vmid']
    
    def get_template_id_by_name(self, template_name: str) -> int:
        if not self.template_exists(template_name):
            raise ValueError(f'Template {template_name} does not exist')
        return self.proxmox_templates[template_name]['vmid']

    def get_all_proxmox_templates(self) -> list:
        templates = {}
        for node in self.api.nodes.get(): 
            if node['node'] == self.settings['primary_node']:
                for vm in self.api.nodes(node['node']).qemu.get():
                    if 'template' in vm and vm['template'] == 1: 
                        templates.update({vm['name']: vm})
        return templates

    def get_all_vms(self) -> dict:
        vms = {}
        for node in self.api.nodes.get(): 
            if node['node'] == self.settings['primary_node']:
                for vm in self.api.nodes(node['node']).qemu.get():
                    if 'template' not in vm or vm['template'] == 0:
                        vms.update({vm['name']: vm})
        return vms
    
    def start_vm(self, vm_name: str) -> str:
        vmid = self.get_vm_id_by_name(vm_name)           
        response = self.api.nodes(self.settings['primary_node']).qemu(vmid).status.start.post()
        logger.info(response)
        return response
                    
    def stop_vm(self, vm_name: str) -> str:
        vmid = self.get_vm_id_by_name(vm_name)           
        response = self.api.nodes(self.settings['primary_node']).qemu(vmid).status.stop.post()
        logger.info(response)
        return response
    
    def reboot_vm(self, vm_name: str) -> str:
        vmid = self.get_vm_id_by_name(vm_name)           
        if not self.is_vm_running(vm_name):
            self.start_vm(vm_name)
            return 'VM started'
        response = self.api.nodes(self.settings['primary_node']).qemu(vmid).status.reboot.post()
        logger.info(response)
        return response
    
    def run_command_on_vm(self, vm_name: str, command: list[str]) -> str:
        vmid = self.get_vm_id_by_name(vm_name)
        node = self.settings['primary_node']
        response = self.api.nodes(node).qemu(vmid).agent.exec.post(command=command)
        logger.info(response)
        pid = response['pid']
        result = self.wait_for_agent_exec_result(vmid, pid)
        return result
                    
    def get_vm_network_info(self, vm_name: str) -> dict:
        ipconfig = self.run_command_on_vm(vm_name, ['ipconfig', '/all']) 
        ipaddress = search('IPv4 Address[\. ]?(?:\. )+: (\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', ipconfig)
        subnetmask = search('Subnet Mask[\. ]?(?:\. )+: (\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3})', ipconfig)
        return {'ip_address': ipaddress.group(1), 'subnet_mask': subnetmask.group(1)}
    
    def is_ip_apipa(self, ip_address: str) -> bool:
        return ip_address.startswith('169.254')
    
    def get_vm_config(self, vm_name: str) -> dict:
        vmid = self.get_vm_id_by_name(vm_name)
        response = self.api.nodes(self.settings['primary_node']).qemu(vmid).config.get()
        return response
    
    def get_template_config(self, template_name: str) -> dict:
        vmid = self.get_template_id_by_name(template_name)
        response = self.api.nodes(self.settings['primary_node']).qemu(vmid).config.get()
        return response

    
    def run_vm_setup(self, vm_name: str) -> str:
        self.start_vm(vm_name)
        wait_until_true(lambda: self.is_agent_running(vm_name))
        new_user = self.run_command_on_vm(vm_name, ['net', 'user', 'remoteuser', 'remoteuser', '/add'])
        logger.info(new_user)
        self.reboot_vm(vm_name)
        wait_until_true(lambda: self.is_agent_running(vm_name))
        while self.is_ip_apipa(self.get_vm_network_info(vm_name)['ip_address']):
            time.sleep(5)
        network_info = self.get_vm_network_info(vm_name)
        logger.info(network_info)

        return new_user

if __name__ == '__main__':
    eng = ProxmoxEngine()