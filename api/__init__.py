from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from api.config import API_PREFIX, CORS_ORIGINS

# Import resources
from api.resources.auth import LoginResource, VerifyTokenResource
from api.resources.patients import PatientResource, PatientListResource
from api.resources.consultants import ConsultantResource, ConsultantListResource
from api.resources.psychiatrists import PsychiatristResource, PsychiatristListResource
from api.resources.screening_tools import (
    ScreeningToolResource, ScreeningToolListResource, ScreeningResultResource
)
from api.resources.listening_templates import ListeningTemplateResource, ListeningTemplateListResource
from api.resources.referrals import ReferralResource, ReferralListResource, PatientReferralsResource

def create_api_app():
    """Initialize the API application"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, resources={f"{API_PREFIX}/*": {"origins": CORS_ORIGINS}})
    
    # Initialize API
    api = Api(app, prefix=API_PREFIX)
    
    # Register authentication resources
    api.add_resource(LoginResource, '/auth/login')
    api.add_resource(VerifyTokenResource, '/auth/verify')
    
    # Register patient resources
    api.add_resource(PatientListResource, '/patients')
    api.add_resource(PatientResource, '/patients/<int:patient_id>')
    
    # Register consultant resources
    api.add_resource(ConsultantListResource, '/consultants')
    api.add_resource(ConsultantResource, '/consultants/<int:consultant_id>')
    
    # Register psychiatrist resources
    api.add_resource(PsychiatristListResource, '/psychiatrists')
    api.add_resource(PsychiatristResource, '/psychiatrists/<int:psychiatrist_id>')
    
    # Register screening tool resources
    api.add_resource(ScreeningToolListResource, '/screening-tools')
    api.add_resource(ScreeningToolResource, '/screening-tools/<int:tool_id>')
    api.add_resource(ScreeningResultResource, '/screening-tools/score')
    
    # Register listening template resources
    api.add_resource(ListeningTemplateListResource, '/listening-templates')
    api.add_resource(ListeningTemplateResource, '/listening-templates/<int:template_id>')
    
    # Register referral resources
    api.add_resource(ReferralListResource, '/referrals')
    api.add_resource(ReferralResource, '/referrals/<int:referral_id>')
    api.add_resource(PatientReferralsResource, '/patients/<int:patient_id>/referrals')
    
    return app

# Create the API application
api_app = create_api_app()