import logging
import os

from lib.helpers import execute, ProcessException


class Scripting:
    def run(self, command, cwd, vars):
        vars_formatted = {}
        for name, value in vars.items():
            variable_name = "VYOS_BUILD_%s" % name.upper()
            vars_formatted[variable_name] = str(value)

        env = os.environ.copy()
        env.update(vars_formatted)

        logging.info("Executing script '%s' with variables: %s" % (command, vars_formatted))
        try:
            execute(command, cwd=cwd, env=env, passthrough=True)
        except ProcessException as e:
            logging.exception(e)
            logging.error("The user script '%s' failed, reason: %s" % (command, str(e)))
            exit(1)
