
from typing import List
import openai
import yaml
import json


with open('conf.yaml','r') as file:
    data  = yaml.safe_load(file)


openai.api_key  = data['OPENAI_API_KEY']

    
class Display:
    @classmethod
    def display_json(cls,data_json):
        json_string  = json.dumps(data_json,indent=4)
        print(json_string)


class Ask:
    @classmethod    
    def parse_instructions(cls,input_string):
        lines = input_string.strip().split('\n')
        instructions = []
        current_id = None
        current_instruction = None
        current_depend_on_id = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("id:"):
                current_id = int(line.split(":")[1].strip())
            elif line.startswith("- instruction:"):
                current_instruction = line.split(":")[1].strip().strip('"')
            elif line.startswith("- depend_on_id_to_run:"):
                current_depend_on_id = line.split(":")[1].strip()
                if current_depend_on_id.lower() == "none":
                    current_depend_on_id = None
                else:
                    current_depend_on_id = int(current_depend_on_id)
            elif line.startswith("[END]"):
                break
            
            if current_id is not None and current_instruction is not None:
                instructions.append((current_id, current_instruction, current_depend_on_id))
                current_id = None
                current_instruction = None
                current_depend_on_id = None
        
        return instructions

    
    @classmethod
    async def ask_chatgpt_for_instructions(cls, sys_prompt, user_prompt):
        messages = [
            {'role':'system', 'content': sys_prompt}, 
            {'role':'user', 'content':user_prompt}
        ]
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        instructions= cls.parse_instructions(completion.choices[0].message.content)
        return instructions
    
    @classmethod
    async def ask_command(cls,messages):
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        return completion.choices[0].message.content

    

class ExcecuteTask:

    @classmethod
    def write_text(cls):
        pass

    @classmethod
    def excute_code(cls):
        pass

    @classmethod
    def web_scrapping(cls):
        pass

    @classmethod
    def search_in_the_web(cls):
        pass

    @classmethod
    def database_operation(cls):
        pass


