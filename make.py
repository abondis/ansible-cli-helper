#!/usr/bin/env python
import cmd
import os
import subprocess
from scripts.ssh import get_hosts, open_ssh
import sys
# add CWD path to sys path to be able to import config.py
sys.path.insert(0, sys.path.insert(0, os.getcwd()))

try:
    from config import ansible_cmd, actions, journalctl, logs, envs
except Exception as e:
    if not os.path.exists('config.py'):
        from shutil import copyfile
        copyfile(
            os.path.join(
                os.path.dirname(__file__),
                "config_sample.py"
            ),
            'config.py'
        )
        print(
            "A new config.py file has been created,"
            " ensure the settings are correct."
        )
        from config import ansible_cmd, actions, journalctl, logs, envs
    else:
        raise e
# Magic!
default_env, = envs[0:1] or [""]

# arguments handling
import argparse
import shlex

# NOTE: does it exist somewhere in the std lib?
def split_n_call(command):
    command = shlex.split(command)
    return subprocess.check_call(command)

action_parser = argparse.ArgumentParser(
    description='Parse actions argumetns'
)
action_parser.add_argument("action", help="Action to call")
action_parser.add_argument("-o", "--opts", nargs="?", help="Command options")
action_parser.add_argument("-l", "--limits",nargs="?",  help="Command limits to append")


def _completer(_func):
    """
    Get a Cmd Completer without having to rewrite a loop every time.
    _func: function returning a list
    """
    def _cmd_complete(
            self,
            text,
            line,
            begidx,
            endidx,
    ):
        # import ipdb
        # ipdb.set_trace()
        fuzz = len(text) >= 3
        results = []
        for i in _func():
            if (fuzz and text in i) or i.startswith(text):
                results.append(i)
        return results
    return _cmd_complete

complete_actions = _completer(actions.keys)


class MainLoop(cmd.Cmd):

    env = default_env
    complete_run = complete_actions
    complete_check = complete_actions
    complete_list = complete_actions
    complete_env = _completer(lambda: envs)
    complete_logs = _completer(logs.keys)

    def _get_hosts(self, limit=None):
        """
        List ansible hosts by environment and optional limit argument
        """
        if limit:
            limit = f"{limit}:&{self.env}"
        else:
            limit = self.env
        hosts = {
            k.name: k
            for k in get_hosts(f"{limit}")
        }
        return hosts

    def complete_ssh(self, *args, **kwargs):
        return _completer(self.hosts.keys)(self, *args, **kwargs)

    def ansible_cmd(self, limit=None):
        """
        Prepare the command string to run ansible
        """
        if limit:
            limit = f"{limit}:&{self.env}"
        else:
            limit = self.env
        return f"{ansible_cmd} -l {limit} "

    def __init__(self):
        super(MainLoop, self).__init__()
        self.do_env(self.env)

    def do_hosts(self, t):
        """
        List environment hosts
        """
        print(self.hosts)

    def do_env(self, env):
        """
        Change environment
        """
        self.env = env
        self.prompt = f"{self.env}> "
        self.hosts = self._get_hosts()

    def do_ssh(self, host):
        """
        SSH into an ansible host for the current environment
        """
        if host in self.hosts:
            open_ssh(self.hosts.get(host), [])

    # NOTE: limits and opts args are used by other commands (ie: do_list)
    def do_run(self, action, opts="", limits=None):
        """
        Run different actions (see action variable at the top of the file)
        """
        # Parse action using argparse
        parsed = action_parser.parse_args(
            shlex.split(action)
        )
        if parsed.action in actions:
            # Add a space ... just in case
            if parsed.opts:
                opts += " " + parsed.opts
            if parsed.limits:
                if limits:
                    limits += ":"
                else:
                    limits = ""
                limits +=  parsed.limits
            command = (
                self.ansible_cmd(limits)
                + opts + " "
                + actions[parsed.action]
            )
            print(command)
            # FIXME: use subprocess?
            split_n_call(command)

    def do_list(self, action):
        """
        List hosts impacted by a chosen action
        """
        self.do_run(action, ' --list-hosts')

    def do_check(self, action, opts="", limits=None):
        """
        Dry run a chosen action
        """
        opt = " --check"
        if opts:
            opts =" ".join(opt, opts)
        else:
            opts = opt

        self.do_run(action, opts, limits)

    def do_exit(self, s):
        """
        Bye
        """
        return True

    def do_logs(self, s, _host=None):
        """
        Show logs on specific service of the selected environment
        See: 'logs' variable at the top of the file
        """
        hosts = get_hosts(f'{self.env}:&{s}')
        print(hosts)
        if hosts:
            if _host in hosts:
                first = _host
            else:
                first = hosts[0]
            open_ssh(first, logs[s])
        else:
            print("No host found")

    def do_shell(self, s):
        """
        Accept ! to run a shell command (ie: '! ls')
        """
        split_n_call(s)

    do_EOF = do_exit

if __name__ == "__main__":
    main = MainLoop()

    import sys
    # FIXME: won't do completion or env change
    if len(sys.argv) > 1:
        main.onecmd(' '.join(sys.argv[1:]))
    else:
        main.cmdloop()
