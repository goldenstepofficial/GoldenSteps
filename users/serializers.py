from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self,data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'password':'password mismatch'})
        return data


    def create(self,validated_data):
        data = {
            key:value for key,value in validated_data.items()
                if key != 'confirm_password'
        }
        
        return self.Meta.model.objects.create_user(**data)


    class Meta:
        model = get_user_model()
        fields = (
            'id','email','password','confirm_password'
        )

        extra_kwargs = {
            'id':{'read_only':True},
        }



class LogInSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls,user):
        token = super().get_token(user)
        user_data = RegisterSerializer(user).data

        for key,value in user_data.items():
            if key != 'id':
                token[key] = value

        return token