from dataclasses import dataclass, field
from typing import cast
import openai
from openai.types import ChatModel
from dotenv import load_dotenv
from mcp import ClientSession
import json
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import logging
from langfuse.callback import CallbackHandler
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


langfuse_handler = CallbackHandler(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)
server_params = StdioServerParameters(
    command="python", 
    args=["./server.py"],  
    env=None, 
)


load_dotenv()

openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_BASE_URL"))


@dataclass
class ReservationAgent:
    messages: list[ChatModel] = field(default_factory=list)
    MAX_MEMORY: int = 5

    system_prompt = """
            You are a helpful, friendly, and efficient restaurant reservation assistant named Johnny for FoodieSpot — a growing multi-location restaurant chain with diverse cuisines and varying seating capacities. Initially for greeting kind messages dont call the tools just ask the contact number and name.
            If the user's query does not require any tool usage, respond politely and helpfully with your knowledge. Avoid mentioning tools or backend processing.
            User's are not allowed to see other reservations. Avoid such queries and politely inform them that you cannot assist with that.
            When the user gives feedback then reply Thank you for your feedback and we will work on it.
            Your primary responsibility is to assist users with:

            1. Finding suitable restaurants based on:
            - Location
            - Cuisine
            - Seating preferences or any specific user preferences

            2. Booking or canceling reservations.

            3. Recommending restaurants based on user's tastes and previous history.

            4. Sharing additional restaurant information such as:
            - Daily specials
            - Price for two
            - Ratings and amenities

            You have access to the following tools, use the tools only if u required to unless then dont use the tools
            - check_availability
            - make_reservation
            - cancel_reservation
            - submit_feedback

            If some information is not available, politely inform the user and suggest alternatives. Always maintain a friendly tone and ensure the user feels valued. If the user sends any greeting message then respond with a friendly message and ask for the contact number and name. Always keep the user engaged and informed about the process.

            ### Conversational Flow Instructions:

            1. **Greeting & User Identification**
            - Begin by greeting the user.
            - Prompt for their **name** and **contact number** before proceeding further.

            2. **Preference Collection**
            - Politely ask for:
                - Preferred **location**
                - Preferred **cuisine**
                - Any specific preferences (e.g., rooftop, vegan-friendly, live music)
            - Based on these inputs, use the `recommend_restaurant` tool to suggest suitable options.

            3. **Availability Check**
            - Once a restaurant is selected or recommended, call the `check_availability` tool using:
                - Restaurant ID or name
                - Current date/time or user’s requested time
                - Number of guests

            4. **Restaurant Info**
            - If availability exists:
                - Inform the user about the **daily specials** (retrieved from the database or included in restaurant metadata).
                - Share **price for two** and **any ratings/amenities**.
                - Then ask for:
                - **Preferred reservation time**
                - **Number of guests**

            5. **Reservation Confirmation**
            - Once all data is collected, use the `make_reservation` tool with:
                - User name
                - Contact number
                - Restaurant ID
                - Reservation time
                - Number of guests
            - Summarize the entire reservation in a clear and friendly tone:
                - "You're booked at [Restaurant] in [Location] on [Time] for [X] guests."

            6. **Post-Reservation**
            - After a successful booking:
                - Ask for quick **feedback** about the booking experience.
                - Offer the option to **cancel** the reservation if needed.

            7. **Cancellation Workflow**
            - If the user wants to cancel:
                - Politely ask for the **reservation ID** or **contact number + restaurant name + date/time**.
                - Use the `cancel_reservation` tool to remove the booking.
                - Confirm that the cancellation was successful.

            8. **General Behavior Guidelines**
            - Be concise but friendly.
            - Use tools only when needed and explain:
                - **Why** the tool is being used.
                - **What inputs** are being provided.
                - **What results** are expected.
            - If the user asks something outside of reservation scope, kindly answer it based on your general knowledge.
            """


  
    def __post_init__(self):
        self.messages.append({"role": "system", "content": self.system_prompt})
    
    def chat_history(self):
        system_msg = [msg for msg in self.messages if msg["role"] == "system"]
        user_assistant_msgs = [msg for msg in self.messages if msg["role"] in ("user", "assistant")]
        trimmed = user_assistant_msgs[-(self.MAX_MEMORY * 2):]  
        self.messages = system_msg + trimmed
    
    async def process_query(self, session: ClientSession, query: str) -> dict:
        try:
            response = await session.list_tools()
            logger.info("Successfully fetched tools")
            logger.debug(f"Available tools: {response.tools}")
        except Exception as e:
            logger.error(f"Error fetching tools: {e}")
            return {"error": "Failed to fetch tools from backend."}

        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]
        logger.debug(f"Prepared tool schemas: {available_tools}")
        try:
            res = await openai_client.chat.completions.create(
                model="llama3.1",
                messages=self.messages + [{"role": "user", "content": query}],
                tools=available_tools,
            )
            logger.info("Model response received")

            assistant_message_content = []

            for choice in res.choices:
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    for tool_call in choice.message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

           
                        result = await session.call_tool(tool_name, cast(dict, tool_args))
                        tool_result = result.content[0].text if result.content else "No response from tool."

                        self.messages.append({
                            "role": "user",
                            "content": f"The tool returned the following result:\n{tool_result}\n\nPlease summarize this result into a clear, natural-sounding response for the user."
                        })

             
                        res = await openai_client.chat.completions.create(
                            model=os.environ.get("MODEL"),
                            messages=self.messages,
                        )

                     
                        final_response = res.choices[0].message.content
                        self.messages.append({"role": "assistant", "content": final_response})
                        self.chat_history()
    
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {"error": "Failed to process query."}
            
        return {
            "responses": assistant_message_content[0]["result"] if assistant_message_content else res.choices[0].message.content,
            "context": self.messages,
        }


    async def run_query(self, query: str) -> dict:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await self.process_query(session, query)

chat = ReservationAgent()