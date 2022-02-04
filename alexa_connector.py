import logging
import json
from sanic import Blueprint, response
from sanic.request import Request
from typing import Text, Optional, List, Dict, Any

from rasa.core.channels.channel import UserMessage, OutputChannel
from rasa.core.channels.channel import InputChannel
from rasa.core.channels.channel import CollectingOutputChannel

logger = logging.getLogger(__name__)

class AlexaConnector(InputChannel):
    """A custom http input channel for Alexa.
    You can find more information on custom connectors in the 
    Rasa docs: https://rasa.com/docs/rasa/user-guide/connectors/custom-connectors/
    """

    @classmethod
    def name(cls):
        return "alexa_assistant"

    # Sanic blueprint for handling input. The on_new_message
    # function pass the received message to Rasa Core
    # after you have parsed it
    def blueprint(self, on_new_message):
        alexa_webhook = Blueprint("alexa_webhook", __name__)

        # required route: use to check if connector is live
        @alexa_webhook.route("/", methods=["GET"])
        async def health(request):
            return response.json({"status": "ok"})

        # required route: defines
        @alexa_webhook.route("/webhook", methods=["POST"])
        async def receive(request):
            # get the json request sent by Alexa
            payload = request.json
            # check to see if the user is trying
            # to launch the skill
            intenttype = payload["request"]["type"]
            session_object = payload.get("session")
            session_id = session_object.get('sessionId')
            user_id = session_object.get('user',{}).get("userId")
            sender_id = user_id + session_id

            # if the user is starting the skill, let them
            # know it worked & what to do next
            if intenttype == "LaunchRequest":
                message = "Hello! You can start by saying 'hi'."
                session = "false"
            else:
                # get the Alexa-detected intent
                intent = payload["request"].get("intent", {}).get("name", "")

                # makes sure the user isn't trying to
                # end the skill
                if intent == "AMAZON.StopIntent":
                    session = "true"
                    message = "Talk to you later"
                else:
                    # get the user-provided text from
                    # the slot named "text"
                    text = payload["request"].get("intent", {}).get("slots",{}).get("text",{}).get("value","")

                    # initialize output channel
                    out = CollectingOutputChannel()

                    # send the user message to Rasa &
                    # wait for the response
                    await on_new_message(UserMessage(text, out,sender_id=sender_id))
                    # extract the text from Rasa's response
                    responses = [m["text"] for m in out.messages]
                    if len(responses) >0:
                        message = " ".join(responses)
                    else:
                        message = "Sorry, can you repeat that please?"
                        logger.error("No Response returned from the Assistant")
                    session = "false"

            # Send the response generated by Rasa back to Alexa to
            # pass on to the user.
            r = {
               "version": "1.0",
               "sessionAttributes": {"status": "test"},
               "response": {
                   "outputSpeech": {
                       "type": "PlainText",
                       "text": message,
                       "playBehavior": "REPLACE_ENQUEUED",
                   },
                   "reprompt": {
                       "outputSpeech": {
                          "type": "PlainText",
                          "text": message,
                          "playBehavior": "REPLACE_ENQUEUED",
                       }
                   },
                   "shouldEndSession": session,
                   },
               }
            return response.json(r)

        return alexa_webhook

