import openai
import requests


class GptSupport:
    def __init__(self):
        self.API_KEY = "gpt_key"
        openai.api_key = self.API_KEY

    def generic_query_simple(self, prompt):
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.API_KEY}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system",
                 "content": "You are a Natural Language Processor that converts a text into a json with your analysis "
                            "of scene from text"},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(endpoint, headers=headers, json=data)
        response_data = response.json()
        reply = response_data["choices"][0]["message"]["content"]

        return reply

    def generic_query(self, prompt):
        completion = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0)
        print
        return completion.choices[0]['text']

    def query_chatgpt(self, prompt):
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.API_KEY}"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system",
                 "content": "You are a Natural Language Processor that converts a text into a json with your analysis "
                            "of scene from text"},
                {"role": "user", "content": f"'{prompt}' " + """"
                Generate a format for the above line like the below one "template": {
            "audio": "<audio_file_location>",
            "sequence_data": {
              "sequence_name": "<sequence_name>",
              "sequence_length": <sequence_length_in_seconds>
            },
            "scene": {
              "lighting": [
                {
                  "type": "<lighting_type>",
                  "location": {
                    "x": <lighting_x_position>,
                    "y": <lighting_y_position>,
                    "z": <lighting_z_position>
                  }
                }
              ],
              "objects": [
                {
                  "reference": "<object_reference>",
                  "location": {
                    "x": <object_x_position>,
                    "y": <object_y_position>,
                    "z": <object_z_position>
                  }
                }
              ],
              "actors": [
                {
                  "name": "<actor_name>",
                  "directory": "<actor_directory>",
                  "location": {
                    "x": <actor_x_position>,
                    "y": <actor_y_position>,
                    "z": <actor_z_position>
                  },
                  "rotation": {
                    "roll": <actor_rotation_roll>,
                    "pitch": <actor_rotation_pitch>,
                    "yaw": <actor_rotation_yaw>
                  },
                  "scale": {
                    "x": <actor_scale_x>,
                    "y": <actor_scale_y>,
                    "z": <actor_scale_z>
                  }
                }
              ],
              "environment": "<environment_name>"
            },
            "characters": [
              {
                "name": "Cookie",
                "location": {
                  "x": <character_x_position>,
                  "y": <character_y_position>,
                  "z": <character_z_position>
                },
                "motions": ["<character_motion_file_location>"],
                "emotions": ["Playful", "Sincere"],
                "audio": "<character_audio_file_location>"
              }
            ],
            "time": "<time_of_day>",
            "dialogues": [
              {
                "character": "Cookie",
                "line": "I always do a double in case they forget and only put in one shot.",
                "sequence": <sequence_number>
              }
            ],
            "camera": {
              "transform": {
                "location": {
                  "x": <camera_x_position>,
                  "y": <camera_y_position>,
                  "z": <camera_z_position>
                },
                "rotation": {
                  "pitch": <camera_rotation_pitch>,
                  "yaw": <camera_rotation_yaw>,
                  "roll": <camera_rotation_roll>
                },
                "scale": {
                  "x": <camera_scale_x>,
                  "y": <camera_scale_y>,
                  "z": <camera_scale_z>
                }
              },
              "start_location": {
                "x": <camera_start_x_position>,
                "y": <camera_start_y_position>,
                "z": <camera_start_z_position>
              },
              "end_location": {
                "x": <camera_end_x_position>,
                "y": <camera_end_y_position>,
                "z": <camera_end_z_position>
              }
            },
            "level_sequence_actor": {
              "auto_play": true
            },
            "render_sequence": {
              "project_path": "<project_path>",
              "output_folder": "<output_folder_path>",
              "output_name": "<output_name>",
              "resolution": {
                "x": <resolution_x>,
                "y": <resolution_y>
              },
              "frame_rate": <frame_rate>,
              "quality": <quality_level>
            }
          }
                """}
            ]
        }
        response = requests.post(endpoint, headers=headers, json=data)
        response_data = response.json()
        reply = response_data["choices"][0]["message"]["content"]
        return reply
