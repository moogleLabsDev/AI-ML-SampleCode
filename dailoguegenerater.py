import os
import random

import boto3
import elevenlabs
import gender_guesser.detector as gender_detector
import loguru
from elevenlabs import Voice, VoiceDesign, Gender, Age, Accent
import loguru
from rest_framework.response import Response
from rest_framework import status
from elevenlabs import Voice, VoiceSettings, generate, set_api_key, play
api_base_url_v1 = os.environ.get("ELEVEN_BASE_URL", "https://api.elevenlabs.io/v1")
from main.models import  Audio


from scene_json_AI_Django import settings


class DialoguesVoiceGenerator:

    def __init__(self):
        # Set up the ElevenLabs client with your API key
        api_key = "key"
        elevenlabs.set_api_key(api_key)
        # Create a gender detector object

        self.detector = gender_detector.Detector()

        # self.client = ElevenLabsUser(api_key)

        # API endpoint and authentication token
        self.url = "https://api.eleven-labs.com/api/text-to-speech"
        # self.url = "https://api.eleven-labs.com/api/v1/voice"
        # Request headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def generate_voice(self, character_name, text, output, timestamp):

        try:
            gender = self.detector.get_gender(character_name)
            if gender in ['female', 'mostly female']:
                gender = Gender.female
            else:
                gender = Gender.male

            print(gender)

            set_api_key('key')
            try:
                audio_object = Audio.objects.get(character_name=character_name.lower())
                char_voice_id= audio_object.audio_id
                audio = generate(
                            text=text,
                            voice=Voice(
                                voice_id=char_voice_id,
                                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)))
                # play(audio) 
                
            except Audio.DoesNotExist:
                print("NOT in the database")
                gender = self.detector.get_gender(character_name)
                if gender in ['female', 'mostly female']:
                    gender = Gender.female
                else:
                    gender = Gender.male
                # Build a voice design object
                design = VoiceDesign(
                    name=character_name,
                    text=f"Hello, my name is {character_name}. I'm your personal assistant, I can help you with your daily tasks and I can also read you the news.",
                    gender=gender,
                    age=Age.young,
                    accent=Accent.british,
                    accent_strength=1.0,
                )
                # # Generate audio from the design, and play it to test if it sounds good (optional)
                audio,audio_id = design.generate1()
                # Convert design to usable voice
                voice = self.from_design(design)
                audio = elevenlabs.generate(
                    text=text,
                    voice=pick_random_pre_made_voice(gender),
                    model="eleven_multilingual_v2"
                )
                audio = elevenlabs.generate(text=text, voice=voice)
                audio_object = Audio(character_name=character_name,audio_id=audio_id,voice_type=gender)
                audio_object.save()

            s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

            bucket_name = "bucket_name"

            file_path = f"{timestamp}/dialogues/{output}.wav"
            try:
                loguru.logger.debug(f"Uploading Audio file {file_path} to S3 bucket.")
                s3_client.put_object(Bucket=bucket_name, Key=file_path, Body=audio)
                loguru.logger.debug(f"Audio uploaded successfully to bucket {bucket_name} as {file_path}")
                return "bucket_path" + file_path
            except Exception as e:
                loguru.logger.debug(f"Error uploading audio to bucket {bucket_name}: {e}")
                return None

            # gender = self.detector.get_gender(character_name)
            # if gender in ['female', 'mostly female']:
            #     gender = "female"
            # else:
            #     gender = "male"
            # payload = {
            #     "text": text,
            #     "voice_model": f"en-US-{gender}"
            # }
            # # Make the API request
            # response = requests.post(self.url, data=json.dumps(payload), headers=self.headers, verify=False)
            #
            # # Check if the request was successful
            # if response.status_code == 200:
            #     # Extract the audio content from the response
            #     audio_content = response.content
            #
            #     # Save the audio to a file
            #     with open(output + ".wav", "wb") as file:
            #         file.write(audio_content)
            #
            #     print(f"Audio file {output} saved successfully.")

        except Exception as e:
            print(f"Error: {str(e)} on {output}")
            # error_message=str(e)
            error_message = "We are facing heavy traffic, So we won't be able to process your request, Try again later."
            loguru.logger.debug("Error: " + str(error_message))
            return Response({'error': error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def add_audio_assets(self, actions, timestamp):
        dialogue_index = 1
        for action in actions:
            if action["type"] == "AUDIO":
                output = f"{action['actor']}{dialogue_index}"
                action["file"] = DialoguesVoiceGenerator().generate_voice(action["actor"], action["content"], output,
                                                                          timestamp)
                if type(action["file"]) is not str:
                    action["file"]=""
                dialogue_index += 1
        return actions

def pick_random_pre_made_voice(gender):
    male_names = [
             "Antoni",
             "Josh",
             "Arnold",
             "Adam",
             "Sam"]
    female_names = ["Rachel",
             "Domi",
             "Bella",
             "Elli"]

    if gender == Gender.female:
        return random.choice(female_names)
    else:
        return random.choice(male_names)



