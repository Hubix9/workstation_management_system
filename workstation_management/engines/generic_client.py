import httpx
import jsonrpcclient

class GenericClient:
    def __init__(self, url):
        self.url = url

    def call(self, method, *args, **kwargs):
        response = httpx.post(
            self.url,
            json=jsonrpcclient.request(method, params={name: value for name, value in kwargs.items()}),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        result = jsonrpcclient.parse(response.json()) 
        match result:
            case jsonrpcclient.Ok(result, id):
                return result
            
            case jsonrpcclient.Error(code, message, data, id):
                raise Exception(f"Error {code}: {message} ({data})")

    
    def start_vm(self, vm_name):
        return self.call('start_vm', vm_name=vm_name)
    
    def stop_vm(self, vm_name):
        return self.call('stop_vm', vm_name=vm_name)
    
    def reboot_vm(self, vm_name):
        return self.call('reboot_vm', vm_name=vm_name)
    
    def create_vm(self, template_name, vm_name):
        return self.call('create_vm', template_name=template_name, vm_name=vm_name)
    
    def delete_vm(self, vm_name):
        return self.call('delete_vm', vm_name=vm_name)
    
    def get_vm_network_info(self, vm_name):
        return self.call('get_vm_network_info', vm_name=vm_name)
    
    def run_command_on_vm(self, vm_name, command):
        return self.call('run_command_on_vm', vm_name=vm_name, command=command)
    
    def is_vm_running(self, vm_name):
        return self.call('is_vm_running', vm_name=vm_name)
    
    def is_agent_running(self, vm_name):
        return self.call('is_agent_running', vm_name=vm_name)
    
    def get_resource_usage(self):
        return self.call('get_node_resource_usage')
    
    def get_vm_config(self, vm_name):
        return self.call('get_vm_config', vm_name=vm_name)
    
    def get_template_config(self, template_name):
        return self.call('get_template_config', template_name=template_name)
    
    def vm_exists(self, vm_name):
        return self.call('vm_exists', vm_name=vm_name)
    
    def get_all_vm_names(self):
        return self.call('get_all_vm_names')
    
if __name__ == '__main__':
    client = GenericClient('http://localhost:5000/api/v1')