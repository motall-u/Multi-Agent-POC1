


class Prompter:

    @classmethod
    def sys_instruction_prompt(cls):
        return f"""
        - Generate only a list of instructions.
        - Each task should be suitable for completion within a reasonable amount of time.
        - Each instruction contain the one main concept word key asked to avoid out of context text generation.
        - Use the format:
            [START]
            id: 0
                - instruction: "..."
                - depend_on_id_to_run: None
            id: 1:
                - instruction: "..."
                - depend_on_id_to_run: 0
            ...

            id n:
                - instruction: "..."
                - depend_on_id_to_run: n-1
            [END]
            id and depend_on_id_to_run are int types and instruction a string. If it depends on nothing, set it to None
       """


    def sub_task_user_prompt(cls,input):
        prompt = f"""

        """
        return None
    
    @classmethod
    def agent_runner_prompt(cls):
        return f"""
        You should write a script in bash to solve the prompt and return only the script. Example:
        - if the prompt is "Create a add.py file.", you 
        will create the bash script to create the file add.py.
        - if the prompt is "write a function to add two element in add.py", you should write a bash script
        to write the generate code in add.py
        - etc..
        - Attention:For the script start with ``` and end with  ```. Each bash script start with #!/bin/bash.
        - Dont comment the code or delete any text not necessary for the code.

       """