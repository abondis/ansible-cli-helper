#!/usr/bin/env python2
# adapted from https://github.com/convidera/ansible-tools
from subprocess import call, sys, os
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.helpers import get_group_vars
from ansible.executor.playbook_executor import PlaybookExecutor

globalinventory=InventoryManager(DataLoader(),'./hosts.yml')

def usage():
    prog = os.path.basename(__file__)
    sys.stderr.write('Usage: {0} HOSTPATTERN\n'.format(prog))
    sys.exit(1)


def get_hosts(pattern):
    res = globalinventory.get_hosts(pattern)
    if len(res) == 0:
        res = globalinventory.get_hosts(pattern + "*")
    if len(res) == 0:
        res = globalinventory.get_hosts("*" + pattern + "*")
    return res


def open_ssh(host, command):
    parameters = ['ssh']
    ansible_vars = host.get_vars()
    ansible_group_vars = get_group_vars(host.get_groups())

    # ansible_user
    #   The default ssh user name to use.
    username = ansible_vars.get('ansible_user') \
        or ansible_vars.get('ansible_ssh_user')

    if username is None:
        username = ansible_group_vars.get('ansible_user') \
            or ansible_group_vars.get('ansible_ssh_user')


    userpasswd = ansible_vars.get('ansible_ssh_pass') or ansible_group_vars.get('ansible_ssh_pass')

    sudopw = ansible_vars.get('ansible_become_pass') or ansible_group_vars.get('ansible_become_pass')

    if username is not None:
        parameters.append('-l')
        parameters.append(username)

    # ansible_ssh_private_key_file
    #   Private key file used by ssh.
    #   Useful if using multiple keys and you don't want to use SSH agent.
    identity_file = ansible_vars.get('ansible_ssh_private_key_file')

    if identity_file is not None:
        path = os.path.expanduser(identity_file)
        path = os.path.expandvars(path)
        path = os.path.abspath(path)

        parameters.append('-i')
        parameters.append(path)

    # ansible_port
    #   The ssh port number, if not 22
    port = ansible_vars.get('ansible_port') or 22

    if port is not None:
        parameters.append('-p')
        parameters.append(str(port))

    # ansible_host
    #   The name of the host to connect to, if different from the alias you
    #   wish to give to it.
    hostname = ansible_vars.get('ansible_host') \
        or ansible_vars.get('ansible_ssh_host') \
        or host.name

    # ansible_ssh_common_args
    #   This setting is always appended to the default command line for
    #   sftp, scp, and ssh. Useful to configure a ``ProxyCommand`` for a
    #   certain host (or group).
    ssh_args = ansible_vars.get('ansible_ssh_extra_args') \
        or ansible_group_vars.get('ansible_ssh_extra_args') or ""

    # ansible_sftp_extra_args
    #   This setting is always appended to the default sftp command line.

    # ansible_scp_extra_args
    #   This setting is always appended to the default scp command line.

    # ansible_ssh_extra_args
    #   This setting is always appended to the default ssh command line.

    parameters.append(hostname)
    parameters.extend(ssh_args.split())
    parameters.extend(command)

    if userpasswd is not None:
        parameters.insert(0, "sshpass -p \"" + userpasswd + "\"" )
        os.system(" ".join(parameters))
    else:
        print(" ".join(parameters))
        os.system(" ".join(parameters))


def main(pattern='*', command=[]):
    hosts = get_hosts(pattern)

    if len(hosts) == 0:
        sys.stderr.write('No hosts found.\n')
        sys.exit(1)

    for host in hosts:
        open_ssh(host, command)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        usage()
    else:
        pattern = sys.argv[1]
        try:
            main(pattern, sys.argv[2:])
        except KeyboardInterrupt:
            pass
