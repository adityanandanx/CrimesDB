from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Incident, Case, Person, CasePerson, Evidence, CaseStatusHistory

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role", "email"]
        read_only_fields = fields


class IncidentSerializer(serializers.ModelSerializer):
    reported_by = UserSerializer(read_only=True)

    class Meta:
        model = Incident
        fields = ["id", "title", "description", "status", "reported_by", "created_at"]
        read_only_fields = ["id", "status", "reported_by", "created_at"]


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "first_name", "last_name", "date_of_birth"]


class PersonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["first_name", "last_name", "date_of_birth"]


class EvidenceSerializer(serializers.ModelSerializer):
    collected_by = UserSerializer(read_only=True)

    class Meta:
        model = Evidence
        fields = ["id", "code", "description", "case", "collected_by", "created_at"]
        read_only_fields = ["id", "collected_by", "created_at"]


class CaseStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = CaseStatusHistory
        fields = ["id", "old_status", "new_status", "changed_at", "changed_by"]
        read_only_fields = fields


class CaseSerializer(serializers.ModelSerializer):
    lead_investigator = UserSerializer(read_only=True)
    incident_id = serializers.PrimaryKeyRelatedField(source="incident", read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "title",
            "description",
            "status",
            "lead_investigator",
            "incident_id",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "case_number",
            "status",
            "lead_investigator",
            "incident_id",
            "created_at",
        ]


class CaseAddPersonSerializer(serializers.Serializer):
    person_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=CasePerson.Role.choices)


class CaseAddEvidenceSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    description = serializers.CharField(allow_blank=True, required=False)


class EscalateIncidentSerializer(serializers.Serializer):
    lead_investigator_user_id = serializers.IntegerField()
