import os

import loguru
import spacy

from . import CameraSupport, CharactersAndObjectsProcessor, LightingSupport, LocationSupport, AssetSupport, update_JSON
from .DialoguesProcessor import DialoguesVoiceGenerator
from transformers import pipeline



class ScriptProcessor:
    def __init__(self):
        self.nlp = spacy.load('en_core_web_trf')
        self.voice_generator = DialoguesVoiceGenerator()
        self.DIALOGUES_DIRECTORY = "dialogues"

    def add_emotions_to_actions(input_data):
    # Load the emotion classification model
        classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

        # Get the actions list
        action_list = input_data['actions']
    

        # Create a new list to store actions with emotions
        actions_with_emotions = []
        actions=[]
        # Loop through each action and add the detected emotion to the action dictionary
        for action in action_list:
            if "action" in action:
            # Extract action properties
                action_type = action['type']
                actor = action['actor']
                start_time = action['start_time']
                end_time = action['end_time']
                action_name = action['action']
                

                # Detect emotion for the action text
                detected_emotion = classifier(action_name)[0]  # The classifier returns a list of predictions, we take the first one

                # Add the detected emotion to the action dictionary
                action['emotion'] = detected_emotion['label']

                # Append the action with the detected emotion to the new list
                actions_with_emotions.append(action)

            else:
                actions_with_emotions.append(action)

            
        # Create a new dictionary with the updated actions list
        # response_json = {
        #     'result': [{
        #         'scene': input_data[0]['scene'],
        #         'actions': actions_with_emotions,
        #         'render_sequence': input_data[0]['render_sequence']
        #     }]
        # }
    # RESPONSE JSON SHOULD STAY AN ARRAY IN THE SCRIPT PROCESSOR

        input_data['actions'] = actions_with_emotions
        return input_data

    def process(self, script, timestamp):
        # Split the script into scenes
        cuts = script.split('CUT TO:')
        dialogue_counter = 1


        response_json = []
        for index, cut in enumerate(cuts):
            scene_data = {}

            scenes = cut.split("\n\n\n")
            # Loop through each scene and extract its data
            for scene in scenes:
                # REQUIRED OUTPUTS
                scene_output = {}
                characters_output = []
                time = ""
                if time == "":
                    time = "dynamic time path from S3"
                else:
                    time
                actions = []
                camera = CameraSupport.create_camera_transform()
                objects = []
                scene_description = None
                # -----------------------------------

                start_of_scene = True
                scene = scene.strip()
                # Parse the scene text with spaCy
                doc = self.nlp(scene)

                characters = []
                dialogues = []

                # Extract the scene location and time of day
                location_type, time_of_day = '', ''
                location = None

                last_character_name_captured = ""
                character = ""

                skip_to_end_of_line = False
                for k, token in enumerate(doc):
                    if skip_to_end_of_line:
                        if "\n" in token.text:
                            skip_to_end_of_line = False
                        continue

                    if token.text in ['INT', 'EXT']:
                        location_type = token.text
                    elif token.text in ['DAY', 'NIGHT']:
                        time_of_day = token.text
                        time = "Morning" if token.text == "DAY" else "Night"

                    elif CharactersAndObjectsProcessor.is_character(k, doc, token):
                        dialogue = ""
                        dialogue_output = ""

                        if token.text not in last_character_name_captured:
                            # To check if its not a character name with multiple words
                            character = CharactersAndObjectsProcessor.get_character_name(k, doc, token)
                            # check if there is a dialogue associated with the character

                            for j in range(k + 2, len(doc)):
                                if doc[j].text == '\n':
                                    # we reached the end of the line
                                    break

                                # dialogue

                                dialogue = doc[j:].text
                                dialogue_output = os.path.join(self.DIALOGUES_DIRECTORY,
                                                               character + str(dialogue_counter))
                                dialogue_counter += 1

                                # scene_data.append({"audio": dialogue_output})

                                if "(" in dialogue:
                                    # we found an Expression in parentheses
                                    start = doc.text.index('(') + 1
                                    end = doc.text.index(')')
                                    expression = doc.text[start:end].strip()
                                break

                        last_character_name_captured = character

                        if dialogue.strip() != "":
                            formatted_dialog = dialogue.strip() if "\n" not in dialogue else dialogue.split("\n")[1]

                            # LOGIC DEPRECATED

                            # self.voice_generator.generate_voice(character, formatted_dialog, dialogue_output)

                            characters_and_object_json = CharactersAndObjectsProcessor.get_characters_and_objects_details_GPT(
                                scene_description)

                            character_attributes = CharactersAndObjectsProcessor.get_character_attributes(character,
                                                                                                          characters_and_object_json)
                            objects = characters_and_object_json["objects"]
                            print("usshbas in ochddd==================>",objects)

                            objects = CharactersAndObjectsProcessor.add_rotation_ant_scale(objects)
                            characters.append(
                                {'name': character,
                                 'emotions': character_attributes[
                                     "emotions"] if character_attributes and "emotions" in character_attributes else [],
                                 'audio': dialogue_output,
                                 "motions": character_attributes[
                                     "motions"] if character_attributes and "motions" in character_attributes else [],
                                 "location": character_attributes[
                                     "location"] if character_attributes and "location" in character_attributes else {}})

                            # dialogue timer
                            actions.append(
                                {"type": "AUDIO", "actor": character, "start_time": dialogue_counter,
                                 # "line": formatted_dialog,
                                 "sequence": dialogue_counter,
                                 "file": dialogue_output})

                        characters_output = characters

                    else:  # if none above , it could be scene description
                        scene_description = doc.text[
                                            k:doc.text.find('\n', k)]  # Extracting from current token to end of line
                        skip_to_end_of_line = True  # skip processing of rest of the tokens

                    if token.text.strip() == "third":
                        if k - 1 >= 0:
                            if doc[k - 1].text == "right":
                                location = LocationSupport.get_location("right third")
                            elif doc[k - 1].text == "left":
                                location = LocationSupport.get_location("left third")

                    if location is None:
                        location = LocationSupport.get_location("center third")

                # Extract the action and description text
                action_text = ''
                for token in doc:
                    if start_of_scene:
                        action_text = scene.strip()
                        break
                if not action_text:
                    try:
                        action_text = scene[scene.index('\n') + 1:].strip()
                    except:
                        action_text = ""

                if action_text != "":
                    # UPDATED JSON

                    loguru.logger.info(
                        f"[ScriptProcessor] JSON Generated. Updating Assets Now.\n Current Objects:\n{objects}")

                    characters = AssetSupport.update_assets_references(self.nlp, characters)
                    objects = AssetSupport.update_assets_references(self.nlp, objects)

                    loguru.logger.debug("[ScriptProcessor] Assets references Updated.")

                    lighting = [LightingSupport.create_pointlight()]

                    characters = LocationSupport.add_default_location(characters)
                    objects = LocationSupport.add_default_location(objects)
                    scene_data["prompt"] = scene
                    
                    scene_data["scene"] = {
                        "environment": "DefaultEnvironment",
                        "time": time,
                        "lighting": lighting,
                        "camera": camera,
                        "objects": objects,
                        "actors": characters,
                    }

                    actions = CharactersAndObjectsProcessor.get_actions(scene)
                    actions = CameraSupport.camera_actions(actions,scene)
                    scene_data["actions"] = actions
                    # actions = CharactersAndObjectsProcessor.camera_actions(actions,scene)
                    # scene_data["actions"] = actions
                    # actions=CharactersAndObjectsProcessor.add_walking_movement(actions, scene)
                    # scene_data["actions"] = actions

                    actions = DialoguesVoiceGenerator().add_audio_assets(actions, timestamp)
                    scene_data["actions"] = actions

                    scene_data["render_sequence"] = {
                        "output_name": f"{timestamp}",
                        "resolution": {
                            "x": 1920,
                            "y": 1080
                        },
                        "frame_rate": 24,
                        "quality": 100,
                        "max_frames": 300
                    }

                loguru.logger.debug(
                    "[ScriptProcessor] Processed Scene Data is (Before Location Processing): " + str(scene_data))
                loguru.logger.debug("[ScriptProcessor] Updating Locations.")
                # scene_data = update_JSON.Update_JSON().process_json(scene_data)
                # scene_data = CharactersAndObjectsProcessor.add_locations_to_actors(scene_data)
                loguru.logger.debug("[ScriptProcessor] Locations Update Done. Output SCENE DATA: " + str(scene_data))
               

                scene_data = CharactersAndObjectsProcessor.add_interacting_actor(scene_data)

                scene_data["scene"]["objects"] = CharactersAndObjectsProcessor.add_attaching_bone_detail(
                    scene_data["scene"]["objects"])

                scene_data = ScriptProcessor.add_emotions_to_actions(scene_data)
                response_json.append(scene_data)
                print("herere in result",response_json)
              
     

        return response_json
