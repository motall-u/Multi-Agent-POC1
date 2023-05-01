import os
import socket
import threading
from typing import List , Tuple
from queue import Queue
import json
from utils import Ask, Display
from prompter import Prompter
from message_type import MessageType
import asyncio
import subprocess
import operator as op

class Agent:
    def __init__(self, agent_id, agent_manager_host, agent_manager_port, start_event) -> None:
        self.__agent_id = agent_id
        self.agent_manager_host = agent_manager_host
        self.agent_manager_port = agent_manager_port
        self.start_event = start_event
        
        self.main_task = None
        self.sub_task_queue = Queue()

        self.agent_memory  = []
        self.agent_manager_exec_history = {
            "exec_hist": [],
            "initial_prompt" : ""
        }

    @property
    def agent_id(self):
        return self.__agent_id
    

    async def send_message(self,message: str) -> None:
        print(f"Agent {self.__agent_id} send this message : {message}")
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.agent_manager_host,self.agent_manager_port))
            client_socket.sendall(message.encode())
            response = client_socket.recv(1024).decode()
            print(f"Agent {self.__agent_id} received response: {response}")
            return response
        
    async def run_task(self,prompt):
        user_initial_prompt = self.agent_manager_exec_history['initial_prompt']  
        exec_history = self.agent_manager_exec_history['exec_hist']
        exec_history = '\n'.join(list(map(op.itemgetter(1),exec_history)))
        if exec_history == []:
            done = f"""Take into account the global context, which is: {user_initial_prompt}. 
                Here's what has already been done: {exec_history}. 
            """
        else:
            done = f"""
                Take into account the global context, which is: {user_initial_prompt}. 
            """
            

        prompt= prompt.join(done)
        messages = [
            {'role':'system', 'content': Prompter.agent_runner_prompt()}, 
            {'role':'user', 'content':prompt}
        ]

        command = await Ask.ask_command(messages=messages)
       
        print("COMMAND:",command)
        try:
            subprocess.run(command,shell=True,check=True)
            return command
        except Exception as e:
            print(e)
        finally:
            return f"We failed to run this {command}. Update the code to ensure it will works succesfully  "
        
    

    async def excecute_agent_subtask(self):
        loop_subtask = True
        if self.sub_task_queue.empty():
            self.sub_task_queue.put(self.main_task) 

        while loop_subtask:
            if not self.sub_task_queue.empty():
                print(f"Excecuting a Task for   for {self.agent_id}") #{self.sub_task_queue.get()}
                executed_cmd = await self.run_task(self.sub_task_queue.get()[1])
                self.agent_memory.append(executed_cmd)
                msg = MessageType.add_to_excecutions_history.value + "-" + str(self.agent_id)
                await self.send_message(msg)
                
            else:
                loop_subtask = False


    async def excecute_task(self):
        self.start_event.wait()
     
        message_and_id = MessageType.depend_on.value + "-" + str(self.agent_id)
        response =  await self.send_message(message=message_and_id)
        if response == MessageType.depend_on_none.value:
            # excecute agent
            await self.excecute_agent_subtask()
        elif response == MessageType.status_not_complete.value:
            #we should wait and retry after 5 seconds
            retry = True
            while retry:
                await asyncio.sleep(10)
                response = await self.send_message(message=message_and_id)
                if response == MessageType.status_complete.value:
                    await self.excecute_agent_subtask()
                    retry = False

        elif response == MessageType.status_complete.value:
            #we should excecute by considering the outputs of the agent it depends on
            await self.excecute_agent_subtask()


class AgentManager:
    def __init__(self, host,port, start_event) -> None:
        self.host = host
        self.port = port
        self.server_socket = None
        self.agents = []
        self.start_event = start_event
        self.prompt = ""
        self.tasks_queue = Queue()
        self.memory = {
            "initial_tasks": None,
            "excecutions_history" : [],
            "initial_prompt" : ""
        }

    def handle_connection(self, conn, addre):
        message = conn.recv(1024).decode()
        response = self.process_message(message=message)
        conn.sendall(response.encode())
        conn.close()
    
    def process_message(self, message):
        print("THE MESSAGE",message.split("-"))
        mes_asked, agent_id = message.split("-")
        agent_id = eval(agent_id)

        message = ""
        if mes_asked == MessageType.depend_on.value:
            print(f"Node {agent_id} ask depends on message")
            print(self.memory['initial_tasks'][agent_id])
            depend_on_id = self.memory['initial_tasks'][agent_id][2]
            if depend_on_id == None:
                return MessageType.depend_on_none.value
            else:
                status = self.memory[depend_on_id]['status']

                if status == 0:
                    return MessageType.status_not_complete.value
                else:
                    return MessageType.status_complete.value

        elif mes_asked == MessageType.add_to_excecutions_history.value:
            self.memory['excecutions_history'] = (agent_id,self.agents[agent_id].agent_memory)
            #update status
            task = self.memory['initial_tasks'][agent_id]
            updated_task = [
                task[0],
                task[1],
                1
            ]
            self.memory['initial_tasks'][agent_id] = updated_task
            # Display.display_json(self.memory)
            return MessageType.add_to_excecutions_history.value
        elif mes_asked == MessageType.get_initial_prompt_and_exec_history.value:
            self.agents[agent_id].agent_manager_exec_history = {
                "exec_hist": self.memory['excecutions_history'],
                "initial_prompt" : self.prompt
            }

            

        return message

    def start_server(self):
        print("Starting the server")
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_socket.bind((self.host,self.port))
        self.server_socket.listen(5)
        self.start_event.set()
        
        try:
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_connection,args=(conn, addr)).start()
        except KeyboardInterrupt:
            print("Server stopped by user :)")
        finally:
            self.server_socket.close()

    async def register_agent(self,agent: Agent)-> None:
        self.agents.append(agent)
        self.memory[agent.agent_id] = {
            "main_task": [],
            "sub_tasks": [],
            "status": 0 # 1 if ok
        }
        print(f"Register agent {agent.agent_id}")
    
    async def store_tasks(self,tasks: List, initial_prompt:str):
        self.memory['initial_tasks'] = tasks
        self.memory['initial_prompt'] = initial_prompt
        self.prompt = initial_prompt


        for i, task in enumerate(tasks):
            self.tasks_queue.put(task)
            print(f"Store task \n * task:{tasks[i]} in the task queue")
    
    async def create_sub_task_for_agent(self, main_task):
        sub_tasks =  await Ask.ask_chatgpt_for_instructions(sys_prompt=Prompter.sys_instruction_prompt() ,user_prompt=main_task[1])
        return sub_tasks

    async def assign_tasks(self):
        for agent in self.agents:
            if not self.tasks_queue.empty():
                agent.main_task = self.tasks_queue.get()
                self.memory[agent.agent_id]["main_task"] = agent.main_task
                agent_sub_tasks = await self.create_sub_task_for_agent(agent.main_task)
                self.memory[agent.agent_id]['sub_tasks'] = agent_sub_tasks
                for sub_task in agent_sub_tasks:
                    agent.sub_task_queue.put(sub_task)
        
        Display.display_json(self.memory)
        

    


    async def start_agent(self):
        for agent in self.agents:
            await agent.excecute_task()


async def main():
    start_event = threading.Event()
    agent_manager = AgentManager("localhost",8000, start_event)
    threading.Thread(target=agent_manager.start_server).start() # Start AgentManager in a separate thread


    # prompt = """
    #     Design and construct an Artificial General Intelligence system named Modou,
    #     specifically engineered to achieve the objective of colonizing the United States of America in a virtual world.
    #     Modou will possess comprehensive system access, 
    #     including features like autonomous driving cars, drones,
    #     and more. The planning and execution of Modou's strategy will strive for perfection,
    #     ensuring meticulous attention to detail and optimal decision-making processes.
    # """

    prompt = "Write me a tutorial in numpy in tutorial.md"

    tasks = []

    while tasks==[]:
        print("Thinking ....")
        tasks =  await Ask.ask_chatgpt_for_instructions(sys_prompt=Prompter.sys_instruction_prompt() ,user_prompt=prompt)
    print("Final Task:" ,tasks)

    for i,task in enumerate(tasks):
        await agent_manager.register_agent(Agent(i,agent_manager_host="localhost", agent_manager_port=8000,start_event=start_event))

    await agent_manager.store_tasks(tasks=tasks,initial_prompt=prompt)
    await agent_manager.assign_tasks()
    await agent_manager.start_agent()



   
if __name__=="__main__":
    asyncio.run(main())