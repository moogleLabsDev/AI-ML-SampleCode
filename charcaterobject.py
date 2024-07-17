import json
import re
import os
import loguru

from main.GptSupport import GptSupport

EMOTIONS = ['joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise']


def get_character_attributes(character_name, responseJSON):
    for character in responseJSON["actors"]:
        if str(character["name"]).lower() == str(character_name).lower():
            return character


def get_characters_and_objects_details_GPT(text):
    gpt = GptSupport()

    # Leaving it here for reference
    # query = f"Analyse the statement and ONLY return a json (no other text) that contains two things. " \
    #         f"The objects mentioned in the text as 'objects' and the characters mentioned in the text as 'actors'." \
    #         f" Objects array and actors' locations for the given text '{text}'. " \
    #         f" choose Character emotion from {EMOTIONS}." \
    #         f"we have a lists to fill prompt template with relative location of objects i-e " \
    #         f"expected_prepositions=['on', 'in', 'at', 'under', 'over', 'beside', 'near', 'by', 'from', 'to', 'into', 'onto', 'out of', 'off']" \
    #         f"expected_relative_locations=['right', 'left', 'top', 'bottom', 'front', 'back', 'inside', 'outside', 'center']." \
    #         f"Fill the field 'prompt' regarding RELATIVE LOCATIONS in the template by using preposition from expected_prepositions " \
    #         f"and location from expected_relative_locations" \
    #         f"template for prompt attribute is " \
    #         f"'<object/actor> is <element from expected_prepositions> <relative location from expected_relative_locations> of <object/actor (Object which was set as default)>.'" \
    #         f"the default object will be mentioned explicitly in the script so pick that and assign relative location prompts of other objects with respect to that object." \
    #         f"Fill the prompt only with relative location info STRICTLY USING ONLY template and not with any other words." \
    #         f"Use the following template for response" + """ {"objects": [
    #         {
    #         "name": "<object_name_reference>",
    #         "prompt":"<prompt>",
    #         "location": {
    #         "x": <x_location>,
    #         "y": <y_location>,
    #         "z": <z_location>
    #         },
    #         <add objects in a list like this>
    #         }
    #         ],
    #         "actors": [
    #         {
    #         "name": "<character_name>",
    #         "prompt":"<prompt>",
    #         "location": {
    #         "x": <x_location>,
    #         "y": <y_location>,
    #         "z": <z_location>
    #         },
    #         "motions": ["<list of motions done by character>"],
    #         "emotions": [<list of emotions>]
    #         }
    #         "
    #         """

    loguru.logger.debug(f"[CharactersAndObjectsProcessor] Input text to GPT. {text}")

    query2 = f"Find the all the person and concrete, tangible objects that person interacts inside the text below " \
             f"and put them in 2 lists of actors=[] and objects=[]," \
             f"give me a json in response and no other words so it can be parsed directly." \
             f"expected_prepositions=['on', 'in', 'at', 'under', 'over', 'beside', 'near', 'by', 'from', 'to', 'into', 'onto', 'out of', 'off']. " \
             f"expected_relative_locations=['right', 'left', 'top', 'bottom', 'front', 'back', 'inside', 'outside', 'center']." \
             f"Use these two lists to generate 'PROMPT' attribute of objects and actors to define relative location as mentioned in template." \
             f"Input text is '{text}'" \
             f"Json output should be of the template:" + """
             {
             "objects": [{
            "name": "<object_name>",
            "prompt": "<this object name> is <expected_preposition> <expected_relative_location> of <name of default or other object>" <do not add prompt if the object is default>
            },
            <add objects in a list like this>
            ],
            "actors": [
            {
            "name": "<character_name>",
            "prompt": "<this character name> is <expected_preposition> <expected_relative_location> of <name of default or other object>" <do not add prompt if the object is default>
            },
            <add other characters in a list like this>
    }
             """

    reply = gpt.generic_query(query2)
    print("dkjjd=======================================",reply)

    loguru.logger.debug(f"[CharactersAndObjectsProcessor] Got Response from GPT. {reply}")
    try:
        response_json = extract_outer_json_from_string(reply)
    except:
        # Retrying one more time
        query_retry = gpt.generic_query(query2)
        response_json = extract_outer_json_from_string(query_retry)

    # add_actors_to_objects(response_json)
    remove_actors_from_objects(response_json)
    remove_prompt_of_default_objects(response_json)
    loguru.logger.debug("[CharactersAndObjectsProcessor] Returning with JSON: " + str(response_json))
    print("jefsehfhawdaajw ajadisudhis asdhaisdfia===============>",response_json)
    return response_json

def remove_actors_from_objects(response_json):

    actors = []
    objects = []
    if "actors" in response_json:
        actors = response_json["actors"]
    if "objects" in response_json:
        objects = response_json["objects"]

    actor_names = [actor['name'] for actor in actors]
    objects[:] = [obj for obj in objects if obj['name'] not in actor_names]


def extract_outer_json_from_string(input_string):
    # Find the first occurrence of { or [
    json_start = input_string.find('{')
    array_start = input_string.find('[')
    start_index = json_start if json_start < array_start else array_start
    is_json_object = True if json_start < array_start else False
    if start_index != -1:
        # Reverse the string and find the last occurrence of }
        reversed_string = input_string[::-1]
        closing_character = "}" if is_json_object else "]"
        end_index = len(input_string) - reversed_string.find(closing_character)

        if end_index != -1:
            # Extract the substring between the first {|[ and last }|]
            result = input_string[start_index:end_index]
            try:
                return json.loads(result)
            except:
                loguru.logger.error(f"Could not parse to json: {result}")

    return None

def remove_prompt_of_default_objects(response_json):
    if response_json["objects"] is not None:
        for object in response_json["objects"]:
            if "prompt" in object and "default" in object["prompt"].lower():
                object["prompt"] = None


def get_characters_and_objects_details(nlp, text):
    objects = []
    characters = []
    places = []
    verb_object = []

    doc = nlp(text)

    # for entity in doc.ents:
    # # Check if the entity is labeled as an object
    # if entity.label_ == "OBJECT":
    #     objects.append(entity.text)
    # # Check if the entity is labeled as a character
    # elif entity.label_ == "PERSON":
    #     characters.append(entity.text)
    # elif entity.label_ == "GPE":
    #     places.append(entity.text)
    for ent in doc.ents:
        # Print the entity text and label
        # print(ent.text, ent.label_)
        if ent.label_ == "PERSON":
            characters.append({"PERSON": ent.text})

    for token in doc:
        # if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
        #     person = token.text
        #     verb = token.head.text
        if token.dep_ == "dobj" and token.head.pos_ == "VERB":
            object_entity = token.text
            verb = token.head.text

            verb_object.append({"VERB": verb, "OBJECT": object_entity})

    overall_objects = objects + places
    output = {"objects": overall_objects,
              "actors": characters
              }
    print(verb_object)

    output_json = json.loads(json.dumps(output))

    return output_json


def add_actors_to_objects(response_json):
    # response_json["objects"] = list(response_json["objects"]) + (list(response_json["actors"]))
    if response_json["actors"] is None:
        return
    for actor in list(response_json["actors"]):
        object_already_present = False

        if response_json["objects"] is None:
            response_json["objects"] = response_json["actors"]
            return

        for object in list(response_json["objects"]):
            if str(actor["name"]).lower() == str(object["name"]).lower():
                object_already_present = True
                break
        if not object_already_present:
            response_json["objects"].append(actor)


def is_character(doc_index, document, tok):
    is_ch = True
    if tok.text.isupper() and doc_index + 1 < len(document):
        print(f"[is_character]: {tok}")
        ch_index = 1
        while True:
            if "\n" in document[doc_index + ch_index].text:
                break
            if not document[doc_index + ch_index].text.isupper() and document[
                doc_index + ch_index].text not in [
                "(",
                ")",
                "\'"]:
                is_ch = False
                break
            ch_index += 1
        return is_ch


def get_character_name(doc_index, document, tok):
    ch_name = tok.text
    ch_index = 1
    while True:
        if "\n" in document[doc_index + ch_index].text:
            break
        ch_name += (document[doc_index + ch_index].text + "_")
        ch_index += 1

    return ch_name


def make_action_prompt(text):
    sample_input = \
        """We see Cookie in the Pie Hole Café as she steps up to Cliff in a medium two shot in center third. Cookie's very close. Cliff's awkward and uncomfortable. Cookie uses her finger to tap Cliff four times in the chest. Cliff's surprised.
    
        COOKIE
        One, two, three, four.
    
        We see Cliff, confused as he tries to figure out the tapping.
    
        COOKIE (CONT'D)
        You're my fourth new friend today."""

    sample_output = """[{"type": "ANIM","actor": "Cookie","start_time": 0,"end_time": 10,"action": "step up"},{"type": "ANIM","actor": "Cookie","start_time": 10,"end_time": 14,"action": "knock"},{"type": "AUDIO","actor": "Cookie","start_time": 10,"end_time": 14,"content": "One, two, three, four."},{"type": "ANIM","actor": "Cookie","start_time": 15,"end_time": 16,"action": "surprise"},{"type": "ANIM","actor": "Cliff","start_time": 16,"end_time": 19,"file": "look around"},{"type": "AUDIO","actor": "Cookie","start_time": 19,"end_time": 26,"content": "You're my fourth new friend today."}]"""

    prompt = f"""I give you a movie script and want you to ONLY return a JSON list that contains dictionary. The output will have only the JSON Parseable list and inside that there is sequence of dict.
    There are 2 types of dict: "ANIM" (to represent an action). Inside that dict there are start_time and end_time that are int, indicate the time of the animation or audio happens, I need you to predict and make the time of that most reasonable with the naration. About the timeline of these dict plz predict that based on the naration of the movie script, and sort asc by the start_time. Field actor is the person associated with that action or saying. Finally, is the field of action that describes the action or field of content to be the speech audio content. Be free to convert the context into action (only verb-based not adjective).
    
    sample input could be: '{sample_input}'
    
    expected output according to the sample input could be:
    {sample_output}
    
    only Return a JSON String.
    IMPORTANT: start_time and end_time should be different from the example and you need to predict those, based on the content or action inside the context.
    Text is 
    {text}"""

    return prompt


def get_actions(text):
    prompt = make_action_prompt(text)

    gpt = GptSupport()

    actions = gpt.generic_query(prompt)

    loguru.logger.debug("Actions GPT Response: \n" + actions)
    try:
        response_json = extract_outer_json_from_string(str(actions))
    except:
        # Trying one more time
        actions = gpt.generic_query(prompt)

        response_json = extract_outer_json_from_string(str(actions))

    print(f"Generated JSON from Actions response: {str(response_json)} ")

    update_animation_assets(response_json)
    return response_json


def update_animation(action):
    animation_assets = ["file_name.fbx"]
    match_dict = {"drink": ["lift", "smell"], "idle": ["playful"], "walk": ["move", "come", " go", " enter", "walk"]}

    action_prompt = action["action"]

    matched_action = None

    action_prompt = action_prompt.lower()

    # Find the matched action based on keywords in the action_prompt
    for pre_defined_action, keywords in match_dict.items():
        for keyword in keywords:
            if keyword in action_prompt:
                matched_action = pre_defined_action
                break
        if matched_action:
            break

    action["file"] = "file_name.gbx"  # default
    if matched_action:
        if matched_action.lower() == "walk":
            action["type"] = "TRANSFORM"
            action["start_time"] = 0
            action["end_time"] = 100
            action["location"] = {
                "x": 1,
                "y": -1,
                "z": 0
            }
            action["rotation"] = {
                "x": 0,
                "y": 0,
                "z": 0
            }
            action["scale"] = {
                "x": 1,
                "y": 1,
                "z": 1
            }

        for asset in animation_assets:
            if matched_action.lower() in asset.lower():
                action["file"] = asset
                break

    return action


def update_animation_assets(actions):
    for action in actions:
        if action["type"] == "ANIM":
            action = update_animation(action)

    return actions


def add_rotation_ant_scale(objects):
    for object in objects:
        object["rotation"] = {
            "x": 0,
            "y": 0,
            "z": 0
        }
        object["scale"] = {
            "x": 1,
            "y": 1,
            "z": 1
        }
    print("wjdhshudsed..........",objects)

    return objects


def add_locations_to_actors(scene_data):
    actors = scene_data["scene"]["actors"]
    objects = scene_data["scene"]["objects"]

    for actor in actors:
        for object in objects:
            if actor["name"].lower() == object["name"].lower():
                actor["rotation"] = object["rotation"]
                actor["scale"] = object["scale"]
                actor["location"] = object["location"]

    scene_data["scene"]['actors'] = actors
    scene_data["scene"]['objects'] = objects
    print("nskdsa in scene data--------->",scene_data)

    return scene_data


def add_interacting_actor(scene_data):
    actors = scene_data["scene"]["actors"]
    objects = scene_data["scene"]["objects"]

    for object in objects:
        for actor in actors:
            if object["prompt"] is not None and actor["name"].lower() in object["prompt"].lower():
                loguru.logger.debug(f"Actor {actor['name']} added to object {object['name']}")
                object["actor"] = actor["name"]
                break

    scene_data["scene"]['objects'] = objects
    return scene_data


def add_attaching_bone_detail(objects):
    pre_defined_associations = {"cup": "mixamorig:RightHandThumb1"}
    for object in objects:
        for key in pre_defined_associations.keys():
            if key in object["name"].lower():
                object["bone_name"] = pre_defined_associations[key]
                break

    return objects


def add_walking_movement(actions, actor):
    walking_action = {
        "type": "TRANSFORM",
        "actor": f"{actions[0]['actor']}",
        "start_time": 0,  # starting of scene
        "end_time": 100,
        "location": {
            "x": 1,
            "y": -1,
            "z": 0
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 1,
            "y": 1,
            "z": 1
        }
    }
    actions.append(walking_action)

    return actions


def add_walk_to_every_actor(actions, actors):
    for actor in actors:
        actions = add_walking_movement(actions, actor)

    return actions

def create_camera_transform(text):
    # text contain input prompt
    text = text
    filenames = "camera_animations/"
    dirs = os.listdir(filenames)
    matching_filenames = []
    file=None
    for filename in dirs:
        #split camera name from there .blend extension
        os.path.splitext(filename)
        camera_name=os.path.splitext(filename)[0]
        
        # Convert filename to lowercase to make the search case-insensitive
        lowercase_filename = camera_name.lower()  
        
        # Check if the lowercase filename appears in the lowercase text
        if lowercase_filename in text:
            matching_filenames.append(lowercase_filename)

        # check for file path of camera angles and return path
        if camera_name in text:
            file_path=filenames+filename
            file=file_path
            
         
    return file

def camera_actions(actions,text1):
    camera_action = {
        "type": "CAMERA_MOVEMENT",
        # "actor": f"{actor}",
        "start_time": 0,  # starting of scene
        "end_time": 100,
        "target_location": {
        "x": -3.3654,
        "y": -1.3493,
        "z": 1.9294
      },
      "location":{
        "x": 1.2677,
        "y": 1.3918,
        "z": 1.5885
      },
      "focal_length": 50
      
    }
    camera_angles = create_camera_transform(text1)  # Call create_camera_transform function    
    camera_action["file"] =camera_angles
    # action.append(camera_action)
    actions.append(camera_action)
    return actions