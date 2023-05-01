from enum import Enum



class MessageType(Enum):
    depend_on = "depend_on"
    depend_on_none = "depend_on_none"
    status_complete   = "status_complete"
    status_not_complete = "status_not_complete"
    add_to_excecutions_history = "add_to_excecutions_history"
    get_initial_prompt_and_exec_history = "get_initial_prompt_and_exec_history"