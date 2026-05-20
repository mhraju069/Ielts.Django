from rest_framework import serializers
from .models import *

class BlogSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    def get_content(self, obj):
        if obj.content:
            return obj.content[:150] + "..."
        return ""
    
    class Meta:
        model = Blog
        fields = '__all__'

    
class BlogDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = '__all__'


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Results
        fields = '__all__'


class MockTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = MockTask
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        if request:
            # Fix Listening Audio URL
            if representation.get('l_set') and 'audio' in representation['l_set']:
                audio_path = representation['l_set']['audio']
                if audio_path:
                    full_url = request.build_absolute_uri(audio_path) if not audio_path.startswith('http') else audio_path
                    if 'ngrok-free.dev' in full_url:
                        full_url = full_url.replace('http://', 'https://')
                    representation['l_set']['audio'] = full_url
            
            # Fix Writing Image URLs
            if representation.get('w_set') and isinstance(representation['w_set'], list):
                for item in representation['w_set']:
                    if 'image' in item and item['image']:
                        image_path = item['image']
                        full_url = request.build_absolute_uri(image_path) if not image_path.startswith('http') else image_path
                        if 'ngrok-free.dev' in full_url:
                            full_url = full_url.replace('http://', 'https://')
                        item['image'] = full_url
                            
        return representation