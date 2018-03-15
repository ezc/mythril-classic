from z3 import *
import re
from mythril.analysis.ops import *
from mythril.analysis.report import Issue
import logging


'''
MODULE DESCRIPTION:

Check for invocations of delegatecall(msg.data) in the fallback function.
'''


def execute(statespace):

    logging.debug("Executing module: DELEGATECALL")

    issues = []
    visited = []

    for call in statespace.calls:

        state = call.state
        address = state.get_current_instruction()['address']

        if (call.type == "DELEGATECALL"):

            if (call.node.function_name == "fallback"):

                stack = call.state.mstate.stack

                meminstart = get_variable(stack[-3])

                if meminstart.type == VarType.CONCRETE:

                    if (re.search(r'calldata.*_0', str(state.mstate.memory[meminstart.val]))):

                        issue = Issue(call.node.contract_name, call.node.function_name, address, "CALLDATA forwarded with delegatecall()", "Informational")

                        issue.description = \
                            "This contract forwards its calldata via DELEGATECALL in its fallback function. " \
                            "This means that any function in the called contract can be executed. Note that the callee contract will have access to the storage of the calling contract.\n"   

                        if (call.to.type == VarType.CONCRETE):
                            issue.description += ("DELEGATECALL target: " + hex(call.to.val))
                        else:
                            issue.description += "DELEGATECALL target: " + str(call.to)

                        issues.append(issue)

                if (call.to.type == VarType.SYMBOLIC):

                    issue = Issue(call.node.contract_name, call.node.function_name, address, call.type + " to a user-supplied address")

                    if ("calldata" in str(call.to)):

                        issue.description = \
                            "This contract delegates execution to a contract address obtained from calldata. "

                    else:
                        m = re.search(r'storage_([a-z0-9_&^]+)', str(call.to))

                        if (m):
                            index = m.group(1)

                        func = statespace.find_storage_write(idx)

                        if (func):
                            issue.description = "This contract delegates execution to a contract address in storage slot " + str(index) + ". This storage slot can be written to by calling the function '" + func + "'. "

                        else:
                            logging.debug("[DELEGATECALL] No storage writes to index " + str(index))

                        issue.description += "Be aware that the called contract gets unrestricted access to this contract's state."
                        issues.append(issue)

    return issues
