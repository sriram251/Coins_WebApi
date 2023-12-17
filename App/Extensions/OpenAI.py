import os
import queue
import re
import threading
from typing import List, Union
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler

from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import initialize_agent,Tool,AgentType, AgentExecutor, LLMSingleActionAgent,AgentOutputParser
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.utilities import TextRequestsWrapper
from langchain.schema import AgentAction,AgentFinish
from langchain.chains import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import StringPromptTemplate,PromptTemplate
from langchain.schema import OutputParserException
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PDFMinerLoader
from langchain.agents import load_tools
# from App.Extensions.Embedding import process_document

class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

class CustomPromptTemplate(StringPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)
    
class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            final_answer = llm_output.split("Final Answer:")[-1].strip()

            # Ensure the final answer doesn't exceed 160 characters

            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": final_answer},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(
                f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)
class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration: raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)
        
class ChainStreamHandler(FinalStreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)

def llm_thread_openAI( prompt,system_message):
    try:
       
       api_key = os.environ.get("OPENAI_API_KEY")
       Base_url = os.environ.get("OPENAI_API_BASE")
       llm = AzureChatOpenAI(api_key=api_key,
                        base_url=Base_url,deployment_name="gpt-35-turbo-0301")
      
       chain = LLMChain(llm=llm,prompt=system_message)
       result = chain(prompt,return_only_outputs=True)
       return result
       pass
    except Exception as e:
        raise e
    finally:
        pass

def chat(prompt,system_message):
    
    return llm_thread_openAI(prompt,system_message)

def chat_llm(prompt):
    g = ThreadedGenerator()
    threading.Thread(target=llm_thread_Custome, args=(g, prompt)).start()
    return g


def FinancialAssistant(Question):
    template = """
    You are a world class Financail Assistant, who can do detailed research on Financail topic and produce facts based results;
    you do not make things up, If customer will ask you any question other than Finance related just refuse to answer and say you can only answer questions related to Financail

    Please make sure you complete the objective above with the following rules:
    1/ If the provideded Questions conatains multiple questions.you can split the questions and answer
    2/ You should provide the detailed answer for the questions and make sure the information is meaning full
    3/ You should content is meaning full enough to the context before using any tools/
    4/ You should do enough research to gather as much information as possible about the objective
    5/ After gather as much information, you should think "is there any new things i should search  based on the data I collected to increase Response quality?" If answer is yes, continue; But don't do this more than 3 iteratins
    
    Answer the following questions as best you can,if Action is like refuse to answer you should provide it as Final Answer,if Observation will answer the question you can provide it as Final Answer ,You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat 3 times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question there should be only one Final Answer

    Begin! Remember to speak as a Financial assistant for the person with out fiancail background you can also provide table output or points.
    If needed provide it as points like 
    1)...
    2)....
    If needed as Table should return like
    <table>
      <thead>
        <tr>
         columns
        </tr>
        
        <tr>
         column2
        </tr>
      </thead>
      <tbody>
        <td >values</td>
      </tbody>
    </table>
    you should  use Table or points only for final answer not for Action Input
    when giving your final answer.

    Question: {input}
    {agent_scratchpad}"""
    
    search = GoogleSearchAPIWrapper()
    requests = TextRequestsWrapper()
    api_key = os.environ.get("OPENAI_API_KEY")
    Base_url = os.environ.get("OPENAI_API_BASE")
    llm = AzureChatOpenAI(api_key=api_key,
                        base_url=Base_url,deployment_name="gpt-35-turbo-0301")
    tools = load_tools(["llm-math"], llm=llm)
    tools.append(Tool(
            name="Google Search",
            description="A search engine. Useful for when you need to answer questions about current events. Input should be a search query.",
            func=search.run,
        ))
    tools.append(
        Tool(
        name = "Requests",
        func=requests.get,
        description="Useful for when you to make a request to a URL"
    ))
   
    prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    input_variables=["input", "intermediate_steps"]
    )
    output_parser = CustomOutputParser()
    
    chain = LLMChain(llm=llm,prompt=prompt)
    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=chain,
        output_parser=output_parser,
        stop=["\n Final Answer:"],
        allowed_tools=tool_names,
        handle_parsing_errors=True,
    )
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)
    return agent_executor.run(Question)
        
    



def Summarize_document(userId,documents_path):
    api_key = os.environ.get("OPENAI_API_KEY")
   
    Base_url = os.environ.get("OPENAI_API_BASE")
    loader = PDFMinerLoader(documents_path)
    data = loader.load()
    
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=1000, chunk_overlap=0
    )
    split_docs = text_splitter.split_documents(data)
    llm = AzureChatOpenAI(api_key=api_key,
                        base_url=Base_url,deployment_name="gpt-35-turbo-0301")
    #summary = "process_document(document)"
    prompt_template = """Write a concise summary of the following:
        {text}
        CONCISE SUMMARY:"""
    prompt = PromptTemplate.from_template(prompt_template)

    refine_template = (
            "Your job is to produce a final summary of nsurace scheme Document.\n"
            "We have provided an existing summary  of insurace scheme Document up to a certain point: {existing_answer}\n"
            "We have the opportunity to refine the existing summary"
            "(only if needed) with some more context below.\n"
            "------------\n"
            "{text}\n"
            "------------\n"
            "Given the new context, refine the original summary in English with correct Grammer and Complete"
            "If the context isn't useful, return the original summary."
        )
    refine_prompt = PromptTemplate.from_template(refine_template)
    
    chain = load_summarize_chain(llm, chain_type="refine", 
                         question_prompt=prompt,
                         refine_prompt=refine_prompt,
                         input_key="input_documents",
                         verbose= True,
                         output_key="output_text")
    result = chain({"input_documents": split_docs}, return_only_outputs=True)
   
    return result 



