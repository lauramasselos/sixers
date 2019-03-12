from rest_framework import serializers

from main.models import Order, Product, ExecutionPlan, LocationUpdate, DotAssociation


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = []


class OrderSerializer(serializers.ModelSerializer):
    # products = ProductSerializer()

    class Meta:
        model = Order
        exclude = []

        extra_kwargs = {
            'table_number': {'read_only': True},
        }



class PlanSerializer(serializers.ModelSerializer):
    steps = serializers.JSONField(source='plan_as_json', read_only=True)

    class Meta:
        model = ExecutionPlan
        exclude = ['plan_parsed']
        extra_kwargs = {
            'id': {'read_only': True},
            'plan_parsed': {'read_only': True},
            'steps': {'read_only': True},
        }


class LocationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationUpdate
        exclude = []


class DotAssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DotAssociation
        exclude = []
