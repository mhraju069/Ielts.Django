from rest_framework import serializers
from .models import *

class PlanSerializers(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id','name', 'duration', 'price']
        
class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.get_name_display', read_only=True)
    plan_duration = serializers.CharField(source='plan.get_duration_display', read_only=True)
    plan_price = serializers.DecimalField(source='plan.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Subscriptions
        fields = ['id', 'user', 'plan', 'plan_name', 'plan_duration', 'plan_price', 'start', 'end', 'active']
        read_only_fields = ['user', 'start', 'end', 'active']