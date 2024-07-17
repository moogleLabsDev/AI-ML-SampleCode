import os
import tempfile
import urllib.request

import boto3
# import bpy
import loguru
import spacy

AWS_ACCESS_KEY_ID = "aws_key"
AWS_SECRET_ACCESS_KEY = "secret_key"
                        

class Update_JSON:
    def __init__(self):
        # TODO: Can upgrade it to use en_core_web_trf model instead
        self.nlp = spacy.load('en_core_web_sm')
        verb_pos_set = ["VERB"]
        self.DIALOGUES_DIRECTORY = "dialogues"

    # find subject, object and relationship
    def split_word(self, sentence):
        # Define lists of prepositions and locations to look for
        prepositions = ['on', 'in', 'at', 'under', 'over', 'beside', 'near', 'by', 'from', 'to', 'into', 'onto',
                        'out of', 'off']
        locations = ['right', 'left', 'top', 'bottom', 'front', 'back', 'inside', 'outside', 'center']
        # Parse the sentence using spaCy
        doc = self.nlp(sentence)
        # Find the subject, object, location, and preposition
        location = None
        preposition = None
        subjects = []
        objects = []
        flg_and = None
        for token in doc:
            if token.dep_ == 'nsubj':  # Find the subject
                subjects.append(token.text)
                flg_and = 'subject'
            elif token.dep_ == 'cc':
                if flg_and == 'subject':
                    flg_and = 'subject_1'
                if flg_and == 'object':
                    flg_and = 'object_1'
            elif token.dep_ == 'conj':
                if flg_and == "subject_1":
                    subjects.append(token.text)
                if flg_and == "object_1":
                    objects.append(token.text)
            elif token.dep_ == 'pobj' and not token.text.lower() in locations:  # Find the object
                objects.append(token.text)
                flg_and = 'object'
            elif token.text in prepositions:  # Find the preposition
                preposition = token.text
            elif token.text.lower() in locations:  # Find the location
                location = token.text.lower()
        # Generate all possible combinations using nested loops
        combin_n = 0
        combinations = []
        for i in subjects:
            for j in objects:
                combinations.append({
                    'subject': j,
                    'object': i,
                    'relate': preposition,
                    'location': location
                })
                combin_n += 1
        return combinations

    def process_json(self, old_json):
        # ###change-----------
        # with open('E:\\myproject\\python\\script\\input_json1.json', 'r') as f:
        #     data = json.load(f)
        # ##Importing the object

        data = old_json
        objects = data['scene']['objects']
        actors = data['scene']['actors']

        # objects = actors + objects

        obj_all = []
        imported_obj_array = []
        i = 0
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

        for obj in objects:
            obj_url = obj['file']
            if obj_url == "":
                continue
            if "prompt" in obj and obj["prompt"] is not None:
                obj_prompt = self.split_word(obj['prompt'])
            else:
                obj_prompt = self.split_word("This is base")
            # obj_location = (obj['location']['x'], obj['location']['y'], obj['location']['z'])
            file_name, file_extension = os.path.splitext(obj_url)
            url = obj_url.replace("https://", "").replace("s3.amazonaws.com/", "")
            parts = url.split("/")
            bucket_name_all = parts[0]
            bucket_name_all = bucket_name_all.split(".")
            bucket_name = bucket_name_all[0]
            parts_url = bucket_name_all[1]
            parts[0] = parts_url
            object_key = "/".join(parts)
            obj_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_key},
                                                       ExpiresIn=3600)
            temp_file_url = ""

            resource_found = True

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:

                loguru.logger.debug(f"Trying to fetch object from : {obj_url} ")
                try:
                    urllib.request.urlretrieve(obj_url, temp_file.name)
                except:
                    resource_found = False
                    loguru.logger.debug(f"Resource at {obj_url} not found.")

                loguru.logger.debug("Temporary file created at:", temp_file.name)
                temp_file_url = temp_file.name
            if not resource_found:
                continue
            new_name = temp_file_url + file_extension
            os.rename(temp_file_url, new_name)
            new_name = temp_file_url.replace('\\', r'\\')
            temp_url = str(temp_file_url) + file_extension
            if file_extension.lower() == ".fbx":
                bpy.ops.import_scene.fbx(filepath=temp_url, axis_forward='-Z', axis_up='Y')
            elif file_extension.lower() == ".obj":
                bpy.ops.import_scene.obj(filepath=temp_url, axis_forward='-Z', axis_up='Y')
            else:
                continue
            imported_objects = []
            for imported_obj in bpy.context.scene.objects:
                obj_name = imported_obj.name
                if obj_name == 'Cube' or obj_name == 'Light' or obj_name == 'Camera':
                    bpy.data.objects.remove(imported_obj, do_unlink=True)
                    continue
                if imported_obj_array == []:
                    imported_objects.append(imported_obj)
                else:
                    for imported_name in imported_obj_array:
                        if obj_name != imported_name:
                            imported_objects.append(imported_obj)
                            continue
            for new_obj in imported_objects:
                new_obj.location = (0, 0, 0)
                new_obj.name = obj['name'] + '_' + new_obj.name
                bpy.context.view_layer.objects.active = new_obj
                item = {
                    'name': new_obj.name,
                    'location': (0, 0, 0),
                    'obj_real': '',
                    'size_val': {
                        'x': 0,
                        'y': 0,
                        'z': 0,
                    },
                    'loc_inf': obj_prompt
                }
                obj_all.append(item)
                imported_obj_array.append(new_obj.name)
        for obj_item in obj_all:
            obj_item['obj_real'] = bpy.data.objects.get(obj_item['name'])
            if obj_item['obj_real'] is not None:
                # Get the mesh data for the object
                mesh = obj_item['obj_real'].data
                # Calculate the dimensions of the mesh
                x_vals = [vert.co.x for vert in mesh.vertices]
                y_vals = [vert.co.y for vert in mesh.vertices]
                z_vals = [vert.co.z for vert in mesh.vertices]
                obj_item['size_val']['x'] = round(max(x_vals) - min(x_vals), 2)
                obj_item['size_val']['z'] = round(max(y_vals) - min(y_vals), 2)
                obj_item['size_val']['y'] = round(max(z_vals) - min(z_vals), 2)
                obj_item['location'] = (
                    round((max(x_vals) + min(x_vals)) / 2, 2), round(-(max(z_vals) + min(z_vals)) / 2, 2),
                    round(min(y_vals), 2))
        # special
        loc_inf_cut_to_0_0 = {'subject': 'bar', 'object': 'Cookie', 'relate': 'in', 'location': 'front'}
        loc_inf_cut_to_1_0 = {'subject': 'table', 'object': 'Cliff', 'relate': 'in', 'location': 'right'}
        loc_inf_cut_to_2_0 = {'subject': 'chair', 'object': 'Cookie', 'relate': 'in', 'location': 'front'}
        loc_inf_cut_to_2_1 = {'subject': 'Cookie', 'object': 'Cliff', 'relate': 'in', 'location': 'right'}
        # replace object
        for item in obj_all:
            if item['loc_inf'] == []:
                continue
            obj_loc_inf = item['loc_inf'][0]
            object_array = []
            subject = None
            if obj_loc_inf == loc_inf_cut_to_0_0:
                for obj_item in obj_all:
                    if obj_loc_inf['object'].lower() in obj_item['name'].lower():
                        obj_item['location'] = (3.34, 1.25, 0.32)
                        loc = obj_item['obj_real'].location
                        # change location
                        loc.x = obj_item['location'][0]
                        loc.y = obj_item['location'][1]
                        loc.z = obj_item['location'][2]
                        # Update the scene to show the change
                        bpy.context.view_layer.update()
            if obj_loc_inf == loc_inf_cut_to_1_0:
                for object in objects:
                    if object['name'] == obj_loc_inf['object']:
                        object['location'] = {"x": 1.67536, "y": -0.818229, "z": 0.32}
            if obj_loc_inf == loc_inf_cut_to_2_0:
                for object in objects:
                    if object['name'] == obj_loc_inf['object']:
                        object['location'] = {"x": 3.67536, "y": -2, "z": 0.32}
            if obj_loc_inf == loc_inf_cut_to_2_1:
                for object in objects:
                    if object['name'] == obj_loc_inf['object']:
                        object['location'] = {"x": 4.67536, "y": -2, "z": 0.32}
            # capture object and subject
            for obj_item in obj_all:
                if obj_loc_inf['object'].lower() in obj_item['name'].lower():
                    object_array.append(obj_item)
                if obj_loc_inf['subject'].lower() in obj_item['name'].lower():
                    subject = obj_item
            # get delta
            if object_array != [] and subject is not None:
                for object in object_array:
                    delta = {
                        'x': 0,
                        'y': 0,
                        'z': 0
                    }
                    # case on
                    if obj_loc_inf['relate'] == 'on':
                        delta['z'] = subject['size_val']['z']
                        if obj_loc_inf['location'] == 'left':
                            delta['x'] = -subject['size_val']['x'] / 4.0
                        if obj_loc_inf['location'] == 'right':
                            delta['x'] = subject['size_val']['x'] / 4.0
                    # case in
                    if obj_loc_inf['relate'] == 'in':
                        delta['z'] = subject['size_val']['z'] / 2
                        if obj_loc_inf['location'] == 'front':
                            delta['y'] = -subject['size_val']['y']
                    # Get the current location
                    loc_obj = subject['location']
                    if object['obj_real'] is not None:
                        loc = object['obj_real'].location
                        # change location
                        loc.x = delta['x'] + loc_obj[0]
                        loc.y = delta['y'] + loc_obj[1]
                        loc.z = delta['z'] + loc_obj[2]
                        # Update the scene to show the change
                        object['location'] = loc
                    bpy.context.view_layer.update()
        for item in objects:
            for item1 in obj_all:
                if item['name'].lower() in item1['name'].lower() and item1['obj_real'] is not None:
                    item["location"] = {}
                    item['location']['x'] = item1['obj_real'].location.x
                    item['location']['y'] = item1['obj_real'].location.y
                    item['location']['z'] = item1['obj_real'].location.z
        print(data)
        return data
