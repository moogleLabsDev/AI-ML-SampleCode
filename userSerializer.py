from rest_framework import serializers
from userModel import User
from django.core.exceptions import ValidationError


class UserLoginDetailSerializer(serializers.ModelSerializer):
    """
    Return the details of Login User.
    """

    class Meta(object):
        model = User
        fields = (
        'id', 'email', 'first_name', 'last_name', 'gender', 'phone_no', 'address', 'image', 'image_name',
        'is_active', 'is_deleted',
        )

class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """
    create/update user .
    """
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'gender', 'dob', 'phone_no', 'address', 'email', 'password', 'otp')
        extra_kwargs = {
            'password': {'write_only': True},
            'otp': {'write_only': True}
        }        

    def create(self, validated_data):
        user = User(
            email=validated_data['email'].lower()
        )
        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.gender = validated_data['gender']
        user.phone_no = validated_data['phone_no']
        user.address = validated_data['address']
        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()

        return user

class UserPasswordSerializer (serializers.ModelSerializer):
    """
    This Serializer is for Update the password of user
    """

    class Meta (object):
        model = User
        fields = ('password',)

    def update(self, instance, validated_data):
        """
        Reset Password
        """
        instance.set_password (validated_data['password'])
        instance.otp = None
        instance.otp_send_time = None
        instance.save ()

        return instance