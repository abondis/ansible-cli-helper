# how to run ansible commands
ansible_cmd = "ansible-playbook -v"

# map action to playbook. This will run against selected environment and limits
# passed to the action
actions = {
    'provision': 'provision.yml',
    'deploy': 'deploy.yml',
    'pull': 'pull.yml',
    'tagged': 'playbook.yml --tags=tagged',
}

# command to run to show logs
log_cmd = ['journalctl', '-b']
live_logs = log_cmd + ['-f']
srvc_llogs = live_logs + ['-u']

logs = {
    'sys': log_cmd,
    'ssh': srvc_llogs + ['ssh'],
}

envs = [
    'dev',
    'test',
    'prod',
]
