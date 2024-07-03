import fastapi_jsonrpc as jsonrpc
import proxmox_engine

app = jsonrpc.API()
api_v1 = jsonrpc.Entrypoint('/api/v1')

engine = proxmox_engine.ProxmoxEngine() 

@api_v1.method()
async def start_vm(vm_name: str) -> str:
    return engine.start_vm(vm_name) 

@api_v1.method()
async def stop_vm(vm_name: str) -> str:
    return engine.stop_vm(vm_name) 

@api_v1.method()
async def reboot_vm(vm_name: str) -> str:
    return engine.reboot_vm(vm_name) 

@api_v1.method()
async def create_vm(template_name: str, vm_name: str) -> str:
    return engine.create_vm(template_name, vm_name)

@api_v1.method()
async def delete_vm(vm_name: str) -> str:
    return engine.delete_vm(vm_name)

@api_v1.method()
async def get_vm_network_info(vm_name: str) -> dict:
    return engine.get_vm_network_info(vm_name) 

@api_v1.method()
async def run_command_on_vm(vm_name: str, command: list[str]) -> str:
    return engine.run_command_on_vm(vm_name, command)

@api_v1.method()
async def is_vm_running(vm_name: str) -> bool:
    try:
        return engine.is_vm_running(vm_name)
    except ValueError:
        return False

@api_v1.method()
async def is_agent_running(vm_name: str) -> bool:
    return engine.is_agent_running(vm_name)

@api_v1.method()
async def get_resource_usage() -> dict:
    return engine.get_resource_usage()

@api_v1.method()
async def get_vm_config(vm_name: str) -> dict:
    return engine.get_vm_config(vm_name)

@api_v1.method()
async def get_template_config(template_name: str) -> dict:
    return engine.get_template_config(template_name)

@api_v1.method()
async def vm_exists(vm_name: str) -> bool:
    return engine.vm_exists(vm_name)

@api_v1.method()
async def get_all_vm_names() -> list[str]:
    return list(engine.get_all_vms().keys())

app.bind_entrypoint(api_v1)